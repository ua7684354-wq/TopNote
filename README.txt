TopNote 1.3 - overlay recovery update
===================================

Prepared for the reported ITEL itel S685LN / Android 15 disappearance issue.
This is a personal test build. The code and package have been checked, but this
update has not run on the user's physical phone or an Android emulator.

QUICK INSTALL
1. Open TopNote-1.3.apk on the phone and choose Update / Install over TopNote.
   Keep the existing app installed so its text and settings are retained.
2. Open TopNote and tap Apply changes (or Show my text).
3. Keep Display over other apps enabled. Allow notifications to see Stop.
4. Your report already shows Battery exemption: true. Also check the separate
   phone app-management controls listed below.
5. Press Home; test lock/unlock and normal use without reopening TopNote.

The APK uses the same package and signing certificate as the uploaded 1.2 APK.
versionCode rises from 3 to 4; versionName is 1.3. An ordinary in-place update
should preserve app preferences. If installation fails, record the installer
message before considering uninstalling, which removes private app data.

WHAT THE ORIGINAL REPORT SHOWS
- Text enabled, overlay permission and Android battery exemption were true.
- "Service running before reopening: true" was TopNote's static flag. It was
  not an operating-system service or rendering health check.
- "Window visible" meant the local view was attached and marked visible.
  Version 1.2 did not check actual draw callbacks.
- Android reason 13 is REASON_OTHER. Its system description is needed for
  further detail. It is not, by itself, evidence of an app crash. The historical
  dates shown do not establish the cause of the latest disappearance.
- Version 1.2 deduplicated repeated states. A long event gap does not prove the
  process was suspended for the entire interval.

The symptom fits wake/window recovery or manufacturer background handling,
but one phone-side cause has not been proven. Version 1.3 addresses concrete
code gaps and records evidence to distinguish these cases if it happens again.

CHANGES IN 1.3

1. Bounded window recovery.
   An awake, unlocked phone receives a relayout/redraw request at most once
   every 30 seconds from the regular timer, plus wake/display events. Actual
   TextView draw callbacks record when the app drew the label.

   If an attached, shown label of nonzero size reports visible window state
   but a requested draw does not arrive for 10 CPU-awake seconds, one window
   replacement is permitted. This budget resets on sleep/lock or explicit
   Show / Apply, not on automatic recovery. System-hidden windows are not
   treated as proof of a stale surface. Protected-screen suppression remains
   effective; a draw callback itself is not proof of compositor visibility.

2. Recovery independent of the service's timer.
   While enabled, one explicit immutable PendingIntent schedules an ordinary
   AlarmManager ELAPSED_REALTIME check for ten minutes later. When Android
   delivers it, the receiver checks the saved choice, permission and user-stop
   history, schedules another check, and requests the foreground service.

   This is INEXACT and NON-WAKING. It does not wake a sleeping phone or keep
   the CPU awake. Android can delay delivery well past ten minutes. It is a
   fallback, not a deadline, and cannot repair a blocked main thread or bypass
   an OEM that refuses background work.

   The existing sticky foreground service, screen/unlock broadcasts, display
   callbacks and quick in-process checks remain. Background-start failures are
   recorded. Delayed retry is retained after temporary foreground-promotion
   failure while text and overlay permission are enabled.

3. Explicit repair when reopening.
   The activity captures diagnostics and requests RECOVER even if the service
   flag is already true. RECOVER preserves a healthy label; Show / Apply can
   replace the style/window. The snapshot precedes this activity's request.
   Android may already have delivered queued callbacks during activity launch.

4. User Stop remains authoritative.
   Hide text, notification Stop, disabled text and lost overlay permission
   cancel recovery. Android Active apps Stop can leave alarms scheduled, so
   recovery checks recent exit records for a newer REASON_USER_REQUESTED stop.
   After that stop or Force stop, open TopNote and tap Show / Apply to resume.

   An enabled 1.2 installation receives a migration baseline once so its old
   stop records do not disable today's enabled note. A future baseline caused
   by moving the wall clock back defers automatic restoration until explicit
   Show / Apply establishes a fresh baseline. Unreadable exit history defers
   restoration of a stopped service; it does not tear down a running service.

5. More informative local diagnostics.
   The report includes 64 dated events, current process importance, notification
   permission/channel state, power saver/idle/background restriction status,
   recovery-check and draw ages, elapsed/CPU-awake gaps, view attachment,
   visibility and dimensions, pending draw age and one-shot repair state.
   Exit entries include reason names/numbers, full timestamps, PID, status,
   importance and bounded system descriptions.

   Note text is not deliberately logged. Current saved note text is redacted
   from event and exit-description strings. Reports stay on the phone and are
   shared only when the user copies them. Review the report before sharing.

PHONE SETTINGS TO CHECK
The reported Android battery exemption does not inspect itel's own app manager.
Use only options present on your phone; menu names vary by software version.

- If Phone Master is installed: Toolbox > Auto-start Management > allow TopNote.
  This path is documented for itel/TECNO/Infinix generally; it is not verified
  for the exact S685LN Android 15 interface.
- If App info offers Background activity / Unrestricted / No restrictions,
  allow TopNote to run in the background.
- If TopNote's Recent apps card offers Lock / Keep open / a padlock, enable it.
- If you use Freezer or automatic cleanup, keep TopNote out of apps it closes
  or freezes. No exact cleanup-exclusion path is verified for this phone.

The label intentionally hides on the lock screen. Android and protected apps
can suppress overlays on sensitive screens. TopNote cannot force visibility
on those screens.

PHONE ACCEPTANCE CHECK
1. Apply text, press Home, and check it while using normal apps.
2. Lock for one minute, unlock, and check without opening TopNote. Repeat with
   your usual fingerprint/PIN unlock method.
3. Test a 30-60 minute screen-off period and several hours of normal use, long
   enough to cover the interval that previously caused disappearance.
4. Reboot and unlock once. Check enabled-text restore when boot/autostart is
   allowed by the phone.
5. Tap Hide text or notification Stop; lock/unlock and wait. Text must stay off.
6. Show text, use Android Active apps > Stop, and check that automatic recovery
   does not re-enable it. Open TopNote and tap Show / Apply to resume.

If text disappears again:
- Note the time and whether it followed unlocking, an app switch, cleanup,
  or a long idle period.
- Before opening TopNote, check whether its foreground notification remains.
  Absence alone is inconclusive if notification permission is disabled.
- Open TopNote and immediately choose Troubleshooting report > Copy report,
  before tapping Apply or leaving the app again.
- Share that report, the disappearance time, and the notification observation.

APP FEATURES AND PERMISSIONS
Shows short text in a floating label below the real system status bar. Text
color, size, alignment, vertical spacing, dark background and bold remain
available. This does not replace the clock/battery/status-bar content.

Runs offline: no account, ads, analytics, internet, accessibility service or
root. No wake lock or exact-alarm permission. The update adds one non-exported
receiver and no new permissions. Minimum Android 8 / API 26; compile and
target SDK remain 34. Host logic tests exercise API 35 branches as well.

BUILD FROM SOURCE
Option A: Android Studio, JDK 17, Android SDK 34, Gradle 8.7, AGP 8.5.2.
Open this folder and sync. A Gradle wrapper is not bundled. Use local Gradle
8.7 or generate the wrapper:
    gradle wrapper --gradle-version 8.7
Build:
    gradle :app:assembleDebug

Option B: Linux manual build (used for the supplied APK).
Requires Python 3, Java 17, SDK Build Tools 34.0.0, SDK Platform 34 and javac
or Eclipse ECJ 3.37.0. Set:
    ANDROID_BUILD_TOOLS=/absolute/path/to/build-tools/34.0.0
    ANDROID_PLATFORM_JAR=/absolute/path/to/platforms/android-34/android.jar
    JAVA_COMPILER_JAR=/absolute/path/to/ecj-3.37.0.jar  (only without javac)
Run:
    python3 build_local.py
Output: build-local/TopNote-1.3.apk
The build script performs no downloads.

Private signing keys are excluded from this updated source archive. The APK
supplied separately is already signed with the original key and can update 1.2.
To rebuild an APK with the same update identity, copy signing/topnote-test.p12
from your original TopNote 1.2 source into the same signing/ path here. The
original key uses alias androiddebugkey and the Android test-key password.
Keep that file private. Without it, the manual build creates a new local test
key, and Android Studio uses its local debug key; either resulting APK has a
different signing identity and cannot update the existing installed app.
Use private production signing and review current distribution requirements
before public release; this is a personal build.

RUN HOST REGRESSION TESTS
    python3 test_persistence.py
Requires Java and javac, or JAVA_COMPILER_JAR pointing to Eclipse ECJ.
Tests compile the actual service, both receivers, settings, recovery and
diagnostics against a controlled fake Android host for API 26, 33, 34 and 35.
They validate lifecycle logic, not real rendering, manufacturer policies,
installation or OS alarm timing.

VALIDATION
See VALIDATION.txt for final build, signature and host-test results.
Physical-device/emulator execution remains untested. This update addresses
identified recovery gaps; it cannot guarantee permanent execution against
Android or manufacturer background restrictions.

REFERENCES
Process exit reasons and descriptions:
https://developer.android.com/reference/android/app/ApplicationExitInfo
Overlay behavior:
https://developer.android.com/reference/android/view/WindowManager.LayoutParams#TYPE_APPLICATION_OVERLAY
Special-use service:
https://developer.android.com/develop/background-work/services/fgs/service-types#special-use
Background service starts:
https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start
Android 15 target-dependent behavior:
https://developer.android.com/about/versions/15/behavior-changes-15
Non-waking alarms and delivery limits:
https://developer.android.com/reference/android/app/AlarmManager#ELAPSED_REALTIME
https://developer.android.com/develop/background-work/services/alarms
Android Active apps Stop:
https://developer.android.com/develop/background-work/services/fgs/handle-user-stopping
Foreground-service notification permission:
https://developer.android.com/develop/ui/views/notifications/notification-permission
Manufacturer-service guidance (menus may vary):
https://www.carlcare.com/ke/tips-detail/speed-up-slow-tecno-phone/
https://www.carlcare.com/ke/tips-detail/Weather-on-Android-Home-Screen/
