#!/usr/bin/env python3
"""
Safe, deterministic executor adapter for Intent Graph leaf nodes.
Provides execute_graph(graph, confirm=False) that maps known actions
(file_scan, static_analysis, report) to local, audit-friendly implementations.
"""
from pathlib import Path
import os
import json
import re
import time

AUDIT_PATH = os.environ.get('OSIRIS_AUDIT_PATH', 'osiris_intent_audit.jsonl')

def _audit_append(entry, audit_path=None):
    path = audit_path or os.environ.get('OSIRIS_AUDIT_PATH', AUDIT_PATH)
    try:
        with open(path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass


def _scan_files(target='.', exts=None, max_files=500):
    if exts is None:
        exts = ['.py', '.sh', '.js', '.md', '.txt']
    files = []
    target = Path(target)
    if not target.exists():
        return files
    for root, dirs, filenames in os.walk(target):
        for fn in sorted(filenames):
            if any(fn.endswith(ext) for ext in exts):
                fp = Path(root) / fn
                try:
                    content = fp.read_text(errors='replace')
                except Exception:
                    content = ''
                files.append((str(fp), content))
                if len(files) >= max_files:
                    return files
    return files


def _analyze_code(files):
    findings = []
    for fname, code in files:
        if 'exec(' in code or 'eval(' in code:
            findings.append({"file": fname, "type": "dynamic_exec", "detail": "use of exec/eval detected"})
        if re.search(r'password\s*=\s*[\"\']', code, re.I):
            findings.append({"file": fname, "type": "hardcoded_secret", "detail": "hardcoded password detected"})
        if 'TODO' in code:
            findings.append({"file": fname, "type": "todo", "detail": "TODO comment present"})
        if 'subprocess' in code:
            findings.append({"file": fname, "type": "subprocess", "detail": "subprocess usage detected"})
        # AST check for syntax errors
        try:
            import ast
            ast.parse(code)
        except Exception as e:
            findings.append({"file": fname, "type": "syntax_error", "detail": str(e)})
    return findings


def execute_graph(graph, confirm=False, report_path='osiris_code_analysis_results.json'):
    """Execute Intent Graph using safe local implementations.
    Returns a list of per-node result dicts similar to the fallback implementation.
    """
    nodes = graph.get('nodes', [])
    results = []
    # context for passing data between nodes
    context = {}

    # Dry-run: enumerate planned actions deterministically
    if not confirm:
        for node in nodes:
            results.append({
                'node': node.get('id'),
                'action': node.get('action'),
                'status': 'dry-run'
            })
        return results

    # Confirmed execution: run known actions in node order
    for node in nodes:
        nid = node.get('id')
        action = node.get('action')

        if action == 'file_scan':
            target = node.get('inputs', {}).get('target', '.')
            files = _scan_files(target)
            context['files'] = files
            results.append({'node': nid, 'action': action, 'status': 'ok', 'files_scanned': len(files)})

        elif action == 'static_analysis':
            files = context.get('files', [])
            findings = _analyze_code(files)
            context['findings'] = findings
            results.append({'node': nid, 'action': action, 'status': 'ok', 'issues': len(findings)})

        elif action == 'report':
            findings = context.get('findings', [])
            files_analyzed = len(set(f.get('file') for f in findings)) if findings else len(context.get('files', []))
            report = {
                'summary': {
                    'files_analyzed': files_analyzed,
                    'issues': len(findings)
                },
                'findings': findings
            }
            try:
                Path(report_path).write_text(json.dumps(report, indent=2))
                results.append({'node': nid, 'action': action, 'status': 'ok', 'report': report_path})
            except Exception as e:
                results.append({'node': nid, 'action': action, 'status': 'error', 'error': str(e)})

        else:
            # Unknown action: mark skipped
            results.append({'node': nid, 'action': action, 'status': 'skipped'})

    # audit execution
    try:
        entry = {
            'type': 'execution',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'graph_root': graph.get('root'),
            'results_summary': {
                'nodes': len(nodes),
                'issues_reported': len(context.get('findings', []))
            },
            'results': results
        }
        _audit_append(entry)
    except Exception:
        pass

    return results
