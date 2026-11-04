# Contributing to TopNote

Thank you for considering helping with TopNote. The project is an Android overlay app, and background behavior is highly dependent on Android version and device manufacturer.

## Before opening a change

- Check existing issues; open a focused feature request before implementing a larger feature.
- For bugs, include the Android version, device model, reproduction steps, observed behavior and expected behavior.
- **Do not share note contents, private reports, phone numbers or other personal data.** Redact diagnostics before attaching them.

## Development

- Use JDK 17, SDK Platform 34, Android Gradle Plugin 8.5.2 and Gradle 8.7 (or Android Studio configured with those versions).
- Keep changes small, documented and connected to a problem or issue.
- Run `python3 test_persistence.py` for changes touching the service, restoration, diagnostics, or recovery behavior.
- If possible, record manual device checks for overlay permission, lock/unlock behavior, user Stop, notification state and reboot.
- Do not commit APKs, signing credentials, generated output or personal diagnostics.

## Pull requests

Describe what changed, why it is necessary, the test evidence, affected Android versions, and any known limitations. Pull requests are reviewed by the maintainer; merge timelines are not guaranteed.

## Licensing

By submitting, you confirm you have the right to contribute your work under the repository's MIT License.
