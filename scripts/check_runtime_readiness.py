"""Print Digital Letter Registry runtime readiness without secret values."""

from __future__ import annotations

import json

from letter_registry.runtime_readiness import check_runtime_readiness


def main() -> int:
    readiness = check_runtime_readiness()
    print(json.dumps(readiness.as_dict(), indent=2))
    return 0 if readiness.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
