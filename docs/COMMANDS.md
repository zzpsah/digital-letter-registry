# Commands

From the repository root:

```bash
git status
git diff
git diff --cached
```

## Tests

This repository uses a `src/` layout. Run tests with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Or install the package in editable mode first and then run unittest discovery.

No production deployment command is defined.
