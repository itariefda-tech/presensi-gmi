# Tools

This folder is for local tooling notes and safe, documented helper scripts.

Ignored local-only folders:

- `tools/local/` for one-off diagnostic scripts.
- `tools/installers/` for downloaded binary installers.
- `tools/backups/` for temporary backup files.

Do not depend on ignored files for app runtime, tests, or deployment. Promote a helper script into a tracked `scripts/` file only after it is parameterized, documented, and safe to run.
