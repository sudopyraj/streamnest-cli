# StreamNest Android

An open-source Android companion app for StreamNest. The APK is a small native
shell around the local StreamNest web interface; `yt-dlp` and FFmpeg continue
to run on the user's computer, so downloads use the user's own network rather
than a shared hosting IP.

## Requirements

- Android Studio Ladybug or newer (Gradle 8.9)
- Android SDK 35
- A running StreamNest companion on a PC in the same Wi-Fi network

## Build the APK

Open this `android-app` directory in Android Studio, allow Gradle to sync, then
choose **Build > Build APK(s)**. The debug APK is written to:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Install from a terminal with:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Every push that changes `android-app/` also runs the **Android APK** GitHub
Actions workflow. Download the generated `streamnest-debug-apk` artifact from
the workflow run if Android Studio is not available.

## Use

On the PC:

```bash
python companion.py --host 0.0.0.0
```

Launch StreamNest on Android and enter the PC's LAN address, such as
`http://192.168.1.25:5000`. Keep both devices on the same trusted Wi-Fi.

The app does not request accounts, passwords, browser cookies, contacts, or
unrelated device permissions. It supports public media only.

## License

This app is released under the repository's MIT license.
