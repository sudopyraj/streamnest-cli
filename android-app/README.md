# StreamNest Android

An open-source Android app for StreamNest. The standalone APK embeds the
`yt-dlp` Python runtime and Android's native media muxer, so public YouTube
downloads can run directly on the phone without a PC. The original
local-companion mode is still available in the main repository for PC-assisted
use.

## Requirements

- Android Studio Ladybug or newer (Gradle 8.9)
- Android SDK 35
- Internet access on the Android device
- Android 10 (API 29) or newer

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

Launch StreamNest on Android, paste a public YouTube URL, select a quality, and
tap **Download**. The app resolves separate video/audio streams and uses
FFmpeg to merge them into an MP4 in the Downloads directory. The app combines compatible MP4 video and M4A audio
tracks without re-encoding.

The app does not request accounts, passwords, browser cookies, contacts, or
unrelated device permissions. It supports public YouTube media only in this
first standalone release. Login-gated, age-restricted, private, CAPTCHA, or
otherwise unavailable media can still fail.

The APK is larger than the companion-only build because it includes Python and
yt-dlp.

## License

This app is released under the repository's MIT license.
