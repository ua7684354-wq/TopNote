<img width="150" height="340" alt="WhatsApp Image 2026-11-04 at 9 21 48 AM (2)" src="https://github.com/user-attachments/assets/e8b8428f-528d-49f5-b181-df0459644491" /> <img width="150" height="340" alt="WhatsApp Image 2026-11-04 at 9 21 48 AM (1)" src="https://github.com/user-attachments/assets/7cadef27-5593-442b-b494-3aa3275b013a" />


# TopNote

**TopNote** is a lightweight, offline Android app that displays a customizable floating text label just below the system status bar. It is designed for people who want a short, persistent on-screen reminder or note while using other apps.

**Current release:** v1.3 · **Platform:** Android 8.0+ (API 26+) · **Application ID:** `app.topnote.personal` · **Language:** Java

> **Project status:** Personal test release. Source-code regression tests have passed, but version 1.3 has not yet been verified on an Android emulator or physical device. Android and manufacturer restrictions can interrupt background services or suppress overlays.

## Features

- Displays user-selected short text in a floating label below the system status bar (it does not replace the system status bar).
- Customize text color, font size, alignment, vertical offset, optional dark background, and bold text.
- Start, hide, or stop the label from the app; a persistent foreground-service notification includes a Stop action.
- Tries to restore enabled text after boot or app update when Android permits it.
- Performs bounded overlay refresh/recovery after screen and unlock events, including a non-waking, inexact background recovery check.
- Provides device-local troubleshooting diagnostics that the user may choose to copy and share.
- Works offline; no account, ads, analytics, internet permission, accessibility service, or root access.

## Android permissions

| Permission | Purpose |
|---|---|
| `SYSTEM_ALERT_WINDOW` | Show the user-enabled floating text over other apps. |
| `POST_NOTIFICATIONS` | Display foreground-service information and controls where permitted. |
| `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE` | Operate the active text overlay service. |
| `RECEIVE_BOOT_COMPLETED` | Attempt to restore the user-enabled label after restart. |
| `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` | Allow a user to request exemption via Android settings; optional and device-dependent. |

Background behavior varies across Android versions and manufacturers. TopNote deliberately hides on lock screens; Android and protected apps may block overlay visibility.

## Get started

**To use a release APK:** Download `TopNote-1.3.apk` from a release published by the maintainer and install it on a supported Android device. Grant **Display over other apps** in Android settings; notification and battery-related settings are optional and can affect background operation. Do not uninstall an existing installation solely to update it, because local settings could be lost. Read the [release notes](README.txt) for important signing and in-place update details.

**To build from source:**

Requirements: Android Studio, JDK 17, Android SDK Platform 34, Android Gradle Plugin 8.5.2, and Gradle 8.7. A Gradle wrapper is **not** included in this repository.

1. Clone this repository and open the root folder in Android Studio.
2. Sync the Gradle project with the above tool versions.
3. Run the `app` configuration or build a debug APK with:

```bash
gradle :app:assembleDebug
```

The build uses your default local Android debug signing key unless you separately supply the original *private* testing key. A differently signed APK cannot update an existing installation in place. **Never commit signing keys or publish a development signing key as a production identity.**

A second local build path (Android SDK command-line tools and `python3 build_local.py`) is described in [the technical release notes](README.txt).

## Tests

Run the source-level host regression suite with Python 3, Java, and `javac`:

```bash
python3 test_persistence.py
```

The suite compiles and tests real service/recovery/diagnostic Java components against simulated Android host APIs. It previously passed **1,327 assertions** covering API-level branches 26, 33, 34, and 35. These are not physical-device, UI, system-integration, or overnight persistence tests; see [validation details](VALIDATION.txt).

## Project layout

```text
app/src/main/                 Android app source, manifest and resources
test_persistence.py           Fake-Android-host regression test suite
build_local.py                Optional offline SDK-based APK build
README.txt                    Detailed v1.3 technical release notes
VALIDATION.txt                Historical build and test validation notes
docs/                         Architecture, testing and release guidance
.github/                      CI and issue templates
```

## Roadmap

These are **planned areas**, not features or guarantees:

- Test actual behavior across representative Android devices, especially devices with aggressive background management.
- Improve installation/setup documentation and publish real app screenshots.
- Make build/release reproducibility easier and expand integration testing.
- Review current Android target-SDK and distribution requirements before wider distribution.

## Contributing

Bug reports, documentation improvements and pull requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md). For suspected security problems, read [SECURITY.md](SECURITY.md).

## License

The repository includes the [MIT License](LICENSE). Contributors should only submit code and assets they have the right to license. The project owner should review and approve this license **before publishing the repository publicly**.
