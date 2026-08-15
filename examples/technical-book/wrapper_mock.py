#!/usr/bin/env python3
"""Tiny deterministic wrapper used only for local smoke tests."""

import json
import sys

prompt = sys.stdin.read()
if 'CHAPTER INDEXES' in prompt:
    print(json.dumps({"issues": [], "summary": "mock"}))
elif '"winner":"A|B|TIE"' in prompt:
    print(json.dumps({"winner": "TIE", "hard_gate": False, "reason": "mock"}))
elif '"candidates"' in prompt:
    print(json.dumps({"candidates": []}))
elif '"claims"' in prompt:
    print(json.dumps({"path": "mock", "claims": [], "definitions": {}, "numbers": [], "owned_concepts": [], "metaphors": [], "cadences": [], "cross_references": []}))
else:
    print(json.dumps({"score": 90, "issues": [], "hard_gate": False, "rationale": "mock"}))
