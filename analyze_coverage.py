#!/usr/bin/env python3
"""Analyze coverage improvements for targeted modules."""

import json

with open('coverage.json') as f:
    data = json.load(f)

print("=== FINAL COVERAGE REPORT ===")
print(f"Overall Optimization Module: {data['totals']['percent_covered_display']}%")
print(f"  Lines: {data['totals']['covered_lines']}/{data['totals']['num_statements']}")
print(f"  Total Files: {len(data['files'])}")
print()

# Filter by module
comp_files = {k: v for k, v in data['files'].items() if 'compression' in k and 'compression' in k.split('/')}
plan_files = {k: v for k, v in data['files'].items() if 'planning' in k and 'planning' in k.split('/')}
par_files = {k: v for k, v in data['files'].items() if 'parallel_executor' in k}
fast_files = {k: v for k, v in data['files'].items() if 'fastapi_integration' in k}

print("=== TARGETED MODULES ===")
for name, files in [
    ("Compression", comp_files),
    ("Planning", plan_files),
    ("Parallel Executor", par_files),
    ("FastAPI Integration", fast_files),
]:
    if files:
        cov = sum(f['summary']['covered_lines'] for f in files.values())
        tot = sum(f['summary']['num_statements'] for f in files.values())
        pct = (cov * 100 / tot) if tot > 0 else 0
        print(f"{name:20s}: {pct:5.1f}% ({cov:4d}/{tot:4d} lines) - {len(files)} files")

print()
print("=== KEY FILES ===")
key_files = [
    'optimization/compression/algorithms.py',
    'optimization/compression/compressor.py',
    'optimization/compression/scoring.py',
    'optimization/planning/reactree.py',
    'optimization/planning/preact.py',
    'optimization/parallel_executor/analyzer.py',
    'optimization/parallel_executor/executor.py',
    'optimization/fastapi_integration.py',
]

for fname in key_files:
    if fname in data['files']:
        f = data['files'][fname]
        print(f"{fname:50s}: {f['summary']['percent_covered_display']:>6s}% "
              f"({f['summary']['covered_lines']:4d}/{f['summary']['num_statements']:4d})")
