#!/usr/bin/env python3
import importlib.util
import inspect
import sys

TEST_FILE = '/home/enki/test_intent_recursive.py'

spec = importlib.util.spec_from_file_location('test_mod', TEST_FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

failed = []
for name, func in inspect.getmembers(mod, inspect.isfunction):
    if name.startswith('test_'):
        try:
            print(f'RUNNING: {name}')
            func()
            print(f'OK: {name}')
        except Exception as e:
            print(f'FAIL: {name} -> {e}')
            failed.append((name, str(e)))

if failed:
    print('\nFAILED TESTS:')
    for n, e in failed:
        print(f'- {n}: {e}')
    sys.exit(1)
else:
    print('\nALL TESTS PASSED')
    sys.exit(0)
