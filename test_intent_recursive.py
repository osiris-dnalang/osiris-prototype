import json
import subprocess
from os import path

from osiris_intent_recursive import decompose, execute_graph


def test_decompose_analyze():
    graph = decompose("Analyze repository for security issues and produce a report", target=".")
    assert isinstance(graph, dict)
    assert 'root' in graph
    actions = [n.get('action') for n in graph.get('nodes', [])]
    assert any(a and 'analyze' in a for a in actions)


def test_execute_dry_run():
    graph = decompose("Analyze repository for security issues and produce a report", target=".")
    res = execute_graph(graph, confirm=False)
    assert isinstance(res, list)
    exec_nodes = [n for n in graph.get('nodes', []) if 'exec' in n]
    if exec_nodes:
        assert any(r.get('status') == 'dry-run' for r in res)


def test_wrapper_intent_dry_run():
    wrapper = path.abspath('./osiris')
    proc = subprocess.run([wrapper, 'intent', '--text', 'Analyze repository for security issues and produce a report', '--dry-run'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0
    out = proc.stdout.strip()
    data = json.loads(out)
    assert 'root' in data


def test_executor_adapter_audit():
    import os
    from os import path as _path
    from osiris_executor_adapter import execute_graph

    audit_path = '/tmp/osiris_audit_test.jsonl'
    report_path = '/tmp/osiris_test_report.json'
    try:
        os.environ['OSIRIS_AUDIT_PATH'] = audit_path
        graph = {'root': 'r1', 'nodes': [
            {'id': 'n1', 'action': 'file_scan', 'inputs': {'target': '.'}},
            {'id': 'n2', 'action': 'static_analysis'},
            {'id': 'n3', 'action': 'report'}
        ]}
        res = execute_graph(graph, confirm=True, report_path=report_path)
        assert isinstance(res, list)
        assert _path.exists(report_path)
        assert _path.exists(audit_path)
        with open(audit_path, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
            assert any('"type": "execution"' in l for l in lines)
    finally:
        try:
            os.remove(report_path)
        except Exception:
            pass
        try:
            os.remove(audit_path)
        except Exception:
            pass
