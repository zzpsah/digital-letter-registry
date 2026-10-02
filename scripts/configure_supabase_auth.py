"""Check/apply hosted Supabase Auth config without exposing credentials."""

from __future__ import annotations

import argparse

from letter_registry.supabase_management import (
    SupabaseAuthConfigManager,
    SupabaseManagementError,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply the checked-in magic-link template and URL config",
    )
    args = parser.parse_args()

    try:
        manager = SupabaseAuthConfigManager.from_environment()
        if args.apply:
            changed = manager.apply()
            print("auth_config=ready")
            print("changed_fields=" + (",".join(changed) if changed else "none"))
            return 0

        drift = manager.check()
        if drift:
            print("auth_config=drift")
            print("drift_fields=" + ",".join(drift))
            return 1
        print("auth_config=ready")
        return 0
    except (ValueError, SupabaseManagementError) as exc:
        print(f"auth_config=error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
