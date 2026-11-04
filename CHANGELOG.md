# Changelog

## 1.3 — 2026-10-20 (personal test release)

- Added bounded refresh/rebuild attempts for potentially stale floating text windows.
- Added a non-waking, inexact scheduled recovery check for previously enabled text.
- Improved explicit repair when reopening the app while preserving the user's Stop/Hide choices.
- Expanded local diagnostics around drawing, process state, alarm delivery and foreground-service behavior.
- Added regression coverage for Android API-level branches 26, 33, 34 and 35.

**Limitations:** Physical-device/emulator runtime verification is still pending; manufacturer-specific background restrictions can prevent reliable recovery.

Detailed version-specific notes are in [README.txt](README.txt). Historical validation is in [VALIDATION.txt](VALIDATION.txt).
