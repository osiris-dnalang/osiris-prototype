#!/usr/bin/env python3
"""
Deterministic Recursive Intent Decomposer (prototype)
- Rule-based top-level routing
- Maps to small Intent Graphs
- Dry-run by default; explicit --execute and --confirm needed to run leaf actions
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
import subprocess


def gen_id():
    return 'n' + uuid.uuid4().hex[:8]


def _match_analyze(text):
    return bool(re.search(r"\b(analyz|scan|vuln|vulnerab|threat|security)\b", text, re.I))


def _match_research(text):
    return bool(re.search(r"\b(research|experiment|study|investigate|discover)\b", text, re.I))

# Audit logging helpers
AUDIT_PATH = os.environ.get('OSIRIS_AUDIT_PATH', 'osiris_intent_audit.jsonl')

def _audit_append(entry, audit_path=None):
    path = audit_path or os.environ.get('OSIRIS_AUDIT_PATH', AUDIT_PATH)
    try:
        with open(path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        # best-effort: do not fail decomposition on audit errors
        pass

def audit_decomposition(graph, rules_applied=None, audit_path=None):
    entry = {
        'type': 'decomposition',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'graph_root': graph.get('root'),
        'original_text': graph.get('original_text'),
        'nodes_count': len(graph.get('nodes', [])),
        'rules_applied': rules_applied if rules_applied is not None else [n.get('source') for n in graph.get('nodes', []) if n.get('source')],
        'decomposer_version': 'osiris_intent_recursive_v1'
    }
    _audit_append(entry, audit_path)

def audit_execution(graph, results, audit_path=None):
    entry = {
        'type': 'execution',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'graph_root': graph.get('root'),
        'execution_results': results
    }
    _audit_append(entry, audit_path)


def decompose(text, target=None):
    text = text.strip()
    nodes = []
    created_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    if _match_analyze(text):
        root_id = gen_id()
        n0 = {
            'id': root_id,
            'type': 'intent',
            'action': 'analyze_repository',
            'description': text,
            'confidence': 0.95,
            'source': 'rule',
            'children': []
        }
        n1_id = gen_id()
        n1 = {
            'id': n1_id,
            'type': 'action',
            'action': 'file_scan',
            'description': 'Scan repository for code files',
            'inputs': {'target': target or '.'},
            'confidence': 0.9,
            'children': []
        }
        n2_id = gen_id()
        n2 = {
            'id': n2_id,
            'type': 'action',
            'action': 'static_analysis',
            'description': 'Run static heuristics (pattern checks, secrets, dangerous calls)',
            'confidence': 0.9,
            'children': []
        }
        n3_id = gen_id()
        demo_path = os.path.join(os.path.dirname(__file__), 'osiris-code-analysis-demo')
        if not os.path.exists(demo_path):
            demo_path = '/home/enki/osiris-code-analysis-demo'
        n3 = {
            'id': n3_id,
            'type': 'action',
            'action': 'report',
            'description': 'Aggregate findings and write report',
            'exec': {'tool': 'osiris-code-analysis-demo', 'path': demo_path, 'args': []},
            'confidence': 0.9,
            'children': []
        }
        # link children
        n0['children'] = [n1_id]
        n1['children'] = [n2_id]
        n2['children'] = [n3_id]
        nodes = [n0, n1, n2, n3]
        graph = {'root': root_id, 'nodes': nodes, 'created_at': created_at, 'original_text': text}
        # Audit decomposition
        try:
            audit_decomposition(graph)
        except Exception:
            pass
        return graph

    elif _match_research(text):
        # minimal research plan graph
        root_id = gen_id()
        n0 = {
            'id': root_id,
            'type': 'intent',
            'action': 'research_proposal',
            'description': text,
            'confidence': 0.85,
            'source': 'rule',
            'children': []
        }
        n1_id = gen_id()
        n1 = {
            'id': n1_id,
            'type': 'action',
            'action': 'literature_scan',
            'description': 'Scan corpus for related work',
            'children': []
        }
        n2_id = gen_id()
        n2 = {
            'id': n2_id,
            'type': 'action',
            'action': 'generate_hypotheses',
            'description': 'Propose 3 testable hypotheses',
            'children': []
        }
        n0['children'] = [n1_id, n2_id]
        nodes = [n0, n1, n2]
        graph = {'root': root_id, 'nodes': nodes, 'created_at': created_at, 'original_text': text}
        # Audit decomposition
        try:
            audit_decomposition(graph)
        except Exception:
            pass
        return graph

    else:
        # fallback single-node graph
        root_id = gen_id()
        n0 = {'id': root_id, 'type': 'intent', 'action': 'unknown', 'description': text, 'confidence': 0.3, 'children': []}
        graph = {'root': root_id, 'nodes': [n0], 'created_at': created_at, 'original_text': text}
        try:
            audit_decomposition(graph)
        except Exception:
            pass
        return graph


def execute_graph(graph, confirm=False):
    """
    Execute leaf nodes that contain exec mapping. Prefer safe adapter when available.
    Requires explicit confirmation.
    """
    # Try safe adapter first (deterministic, audit-friendly)
    try:
        from osiris_executor_adapter import execute_graph as adapter_execute_graph
        res = adapter_execute_graph(graph, confirm=confirm)
        # audit execution if running confirmed
        if confirm:
            try:
                audit_execution(graph, res)
            except Exception:
                pass
        return res
    except Exception:
        # Adapter not available or failed — fall back to subprocess execution
        pass

    results = []
    for node in graph.get('nodes', []):
        exec_info = node.get('exec')
        if exec_info:
            cmd_path = exec_info.get('path')
            args = exec_info.get('args', [])
            cmd = [cmd_path] + args
            if not confirm:
                results.append({'node': node['id'], 'cmd': cmd, 'status': 'dry-run'})
            else:
                try:
                    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
                    results.append({'node': node['id'], 'cmd': cmd, 'exit': proc.returncode, 'output': proc.stdout})
                except Exception as e:
                    results.append({'node': node['id'], 'cmd': cmd, 'error': str(e)})
    # audit fallback execution when confirmed
    if confirm:
        try:
            audit_execution(graph, results)
        except Exception:
            pass
    return results


def main():
    p = argparse.ArgumentParser(description='OSIRIS Intent Recursive Decomposer (prototype)')
    p.add_argument('--text', required=True, help='Natural language instruction')
    p.add_argument('--target', default='.', help='Target path (e.g., repo root)')
    p.add_argument('--execute', action='store_true', help='Execute leaf actions (requires --confirm)')
    p.add_argument('--confirm', action='store_true', help='Confirm destructive/interactive actions (required with --execute)')
    args = p.parse_args()

    graph = decompose(args.text, target=args.target)
    print(json.dumps(graph, indent=2))

    if args.execute:
        if not args.confirm:
            print('\n✗ Execution requires --confirm. Aborting execution (dry-run).')
        else:
            print('\n→ Executing leaf actions (confirmed)')
            res = execute_graph(graph, confirm=True)
            print(json.dumps({'execution_results': res}, indent=2))
    else:
        print('\nℹ Dry-run: use --execute --confirm to run leaf actions')


if __name__ == '__main__':
    main()
