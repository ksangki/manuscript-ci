# Contributing

Manuscript CI should stay conservative. A feature is useful only if it helps authors find real defects without turning their work into generic model-written prose.

## Principles

- The original wins ties.
- No fabricated facts, quotes, citations, experiences, or numbers.
- Prefer report-only automation over silent manuscript writes.
- Provider adapters should remain optional; the core should not require one AI vendor.
- Tests should cover exact-replacement safety and decision logic before new automation is added.

## Development

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m manuscript_ci.cli --help
```

When packaging normally:

```bash
pip install -e . pytest
pytest -q
```
