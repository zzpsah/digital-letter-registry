# Tests — UI Governance

For UI/behavior changes, minimum checks:
- extract inline JavaScript and run `node --check`;
- run full Python unit suite;
- run `git diff --check`;
- verify key live elements on `https://eletters.vercel.app` after Vercel deploy.

Regression expectations include Language/Hinglish default, Smart Search, Remember me, Hinglish card priority, Trash/Restore, recipient single-channel behavior and Operations Retry/Retire/Delete.
