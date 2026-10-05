# Current State — UI Governance

The accepted live baseline includes:

- Purple compact visual system; no wholesale redesign.
- Top navigation: Home, Search, Upload, Admin, Account.
- Top-right Language selector: Hinglish (default), हिन्दी, English.
- Smart Search uses text/fuzzy plus semantic embeddings when available, with non-AI fallback.
- Home quick-search is temporary; Search-tab search is persistent in Search.
- Recent cards prefer Hindi/Hinglish summary/action in default mode.
- Login has Remember me on this device, checked by default.
- Approved accounts use admin-controlled approval and the current initial-password policy.
- Admin Users supports role/status, Set password, Delete user.
- Recipient allows Email-only, WhatsApp-only, or both; available channel(s) auto-enable.
- Recipients have View/Save/Make default/Remove and removed Restore/permanent delete.
- Letter Delete means recoverable Trash; Admin Trash provides Restore/permanent delete.
- Failed jobs have Retry/Retire/Delete.
- Important documents use compact star + yellow highlight; internal comments are not public.
- Default document ordering is latest upload first.

Do not change these as cleanup/refactor side effects.
