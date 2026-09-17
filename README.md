<div align="center">

# StreamNest

**A local-first, open-source media downloader for public YouTube and Instagram media.**

StreamNest provides a guided terminal experience, a small local web interface, a
browser-based PC companion, and an experimental standalone Android application.

<p>
  <a href="https://github.com/sudopyraj/streamnest-cli">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=flat-square&logo=github" alt="GitHub repository">
  </a>
  <a href="https://github.com/sudopyraj/streamnest-cli/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT License">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10 or newer">
  </a>
  <a href="https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.2-android">
    <img src="https://img.shields.io/badge/Android-Experimental-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Experimental Android release">
  </a>
</p>

<p>
  <a href="#installation">Install</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#android-application">Android</a> ·
  <a href="#contributing">Contributing</a> ·
  <a href="https://github.com/sudopyraj/streamnest-cli/releases">Releases</a>
</p>

</div>

> **Scope:** StreamNest is designed for publicly accessible media from supported
> YouTube and Instagram URLs. It is not a hosted download service and does not
> intentionally bypass authentication, CAPTCHA, DRM, or other access controls.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Launching StreamNest](#launching-streamnest)
- [Usage](#usage)
- [Audio](#audio)
- [Playlists](#playlists)
- [Resume support](#resume-support)
- [History](#history)
- [Settings](#settings)
- [Web interface](#web-interface)
- [PC companion](#pc-companion)
- [Android application](#android-application)
- [Advanced CLI](#advanced-cli)
- [Development](#development)
- [Project structure](#project-structure)
- [Security and privacy](#security-and-privacy)
- [Access-control boundaries](#access-control-boundaries)
- [Responsible use](#responsible-use)
- [Contributing](#contributing)
- [Bug reports](#bug-reports)
- [License](#license)
- [Disclaimer](#disclaimer)
- [Project philosophy](#project-philosophy)

## Features

### Interactive CLI

The primary desktop interface is an interactive terminal application with the
following top-level menu:

```text
Download Media
Audio Only
Download Playlist
Download History
Settings
Help
Exit
```

### Supported media workflows

- Public YouTube videos, Shorts, live URLs, and playlists
- Public Instagram posts, reels, and IGTV URLs
- Video downloads with source-dependent format and resolution choices
- Audio-only downloads
- Optional public subtitle download and embedding for supported YouTube media
- Playlist downloads of all items or a selected subset

### Quality and download controls

- Best, balanced (up to 1080p), or small-file (up to 480p) modes
- Custom resolution, frame-rate, and container selection
- Format inspection before downloading
- Maximum file-size selection
- MP4, WebM, or original video output where the source supports it
- Progress information including size, speed, and estimated remaining time
- Bounded fragment and playlist concurrency

### Local management

- Resume prompts for interrupted `.part` and `.ytdl` downloads
- SQLite download history with viewing, searching, and clearing
- Configurable download directory, quality, formats, concurrency, overwrite
  behavior, filename template, and terminal theme
- Local configuration and history; no StreamNest account is required

## Requirements

For the desktop application:

- Python 3.10 or newer
- Internet access
- FFmpeg for merging separate streams, audio conversion, and subtitle
  embedding when those operations are needed

Basic single-stream downloads may work without FFmpeg. StreamNest detects
FFmpeg from `PATH` and common system locations.

## Installation

The package metadata defines both `streamnest` and `media-dl` console commands.
The following instructions install the project in an isolated virtual
environment.

### Linux / macOS

```bash
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

### Windows PowerShell

```powershell
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell blocks activation, use the Python executable inside `.venv`
directly or apply the execution-policy change appropriate for your environment.

### FFmpeg

FFmpeg is optional for simple downloads but recommended for the full feature
set. The project displays platform-specific installation guidance when it is
needed.

<details>
<summary>Common installation commands</summary>

```bash
# Debian / Ubuntu
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# macOS with Homebrew
brew install ffmpeg
```

On Windows, the project suggests:

```powershell
winget install Gyan.FFmpeg
```

</details>

## Launching StreamNest

After installation, start the interactive desktop CLI with either installed
command:

```bash
streamnest
```

or:

```bash
media-dl
```

When running directly from a checkout, use:

```bash
python main.py
```

The installed console commands and `python main.py` all start the same
interactive CLI.

## Usage

The normal workflow is:

1. Start StreamNest.
2. Select an option.
3. Enter a supported public URL.
4. Review the retrieved metadata.
5. Select a quality or format.
6. Select a container or audio format when available.
7. Confirm the download.
8. Monitor the progress display.
9. Open the completed file path shown by StreamNest.

For a video, choose **Download Media**, then choose one of:

- **Best Quality**
- **Balanced (up to 1080p)**
- **Small File (up to 480p)**
- **Custom**
- **Maximum file size**
- **Choose from format list**

When subtitles are available for a supported YouTube video, StreamNest can
download them and optionally embed them into the output. Subtitle embedding
requires FFmpeg.

## Audio

Choose **Audio Only** from the interactive menu. The available quality choices
are best available, 320 kbps, 256 kbps, 192 kbps, and 128 kbps, subject to the
source.

Supported output choices are:

```text
MP3
M4A
Opus
Original (no conversion)
```

Converting to MP3, M4A, or Opus requires FFmpeg. Selecting **Original** avoids
conversion and keeps the source audio format where possible.

## Playlists

Choose **Download Playlist**, paste a supported playlist URL, and select either
**Download all** or **Select videos**. Selection input accepts one-based item
numbers, ranges, or a comma-separated combination:

```text
1-5,7,10-12
```

This selects items 1 through 5, item 7, and items 10 through 12. You can then
apply best, balanced, small-file, or custom video quality to the selected
items. Playlist work uses the configured bounded concurrency rather than an
unlimited number of workers.

## Resume support

The desktop downloader enables yt-dlp continuation and keeps interrupted
partial files. If StreamNest finds matching `.part` or `.ytdl` files in the
configured download directory, the interactive flow shows their rough progress
and offers to resume or remove them.

Resume behavior depends on the source and the files still being compatible.

## History

StreamNest records local download metadata in SQLite. The history menu can:

- View recent downloads
- Search by title, URL, or platform
- Clear all entries after confirmation
- Show recorded total size

The default database is:

```text
~/.local/share/media-downloader/history.sqlite3
```

`XDG_DATA_HOME` or `MEDIA_DOWNLOADER_DATA_DIR` can change the data location.
History stores metadata such as URL, title, platform, timestamp, selected
format, output path, and file size; it does not read or persist passwords,
tokens, or browser cookies.

## Settings

The interactive **Settings** menu supports:

| Setting | Values or purpose |
| --- | --- |
| Download directory | Defaults to `~/Downloads` |
| Default video quality | `best`, `2160p` through `240p` |
| Default audio quality | `best`, `320`, `256`, `192`, `128` |
| Default audio format | `mp3`, `m4a`, `opus`, `original` |
| Default video format | `mp4`, `webm`, `original` |
| Maximum concurrent downloads | Integer from 1 to 8 |
| Overwrite existing files | Enabled or disabled |
| Filename template | A safe filename-only yt-dlp template |
| Theme | `dark`, `light`, or `mono` |

The default configuration file is:

```text
~/.config/media-downloader/config.toml
```

`XDG_CONFIG_HOME` or `MEDIA_DOWNLOADER_CONFIG_DIR` can change the configuration
location. Settings can also be inspected or changed with the `config`
subcommand; see [Advanced CLI](#advanced-cli).

## Web interface

StreamNest includes a lightweight Flask web interface. From the repository
root, start it with:

```bash
flask --app main:app run
```

Then open <http://127.0.0.1:5000>.

The interface accepts public YouTube and Instagram URLs, displays metadata, and
offers the supported video and audio choices exposed by the web implementation.
It runs locally and is not intended to be a centralized public download
service. Long-running or large downloads may be unsuitable for a hosted
environment because they depend on the machine running the Flask process.

## PC companion

`companion.py` runs the same web application as a local companion service:

```bash
python companion.py
```

By default it binds to `127.0.0.1` on port 5000, so it is reachable only from
the computer running it. To let another device on a trusted local network use
the companion, explicitly bind to all interfaces:

```bash
python companion.py --host 0.0.0.0
```

On the other device, open:

```text
http://<computer-lan-ip>:5000
```

> **Security warning:** `--host 0.0.0.0` makes the service reachable on the
> computer's network interfaces. Use it only on a trusted network. The
> companion has no built-in user authentication or transport encryption; do not
> expose it directly to the public internet.

## 📱 Android application

The repository documents two separate Android workflows. They have different
architectures and capabilities.

### Android Companion

The Android companion workflow uses a phone or tablet browser to connect to the
PC companion:

```text
Phone or tablet browser
          │ local network
          ▼
Computer running `python companion.py`
          │
          ▼
        Internet
```

The computer runs StreamNest and performs the download. Start the companion
with `python companion.py`; use `--host 0.0.0.0` only on a trusted local
network. This browser-based workflow is separate from the standalone APK.

### Standalone Android Application

> 🧪 **Experimental**

The `android-app/` project runs a small downloader directly on Android. Basic
downloads can work successfully, but larger downloads and longer videos are
currently less reliable and may take an impractical amount of time. The
desktop CLI remains the primary development target. The standalone APK is
provided primarily for testing and experimentation, not as a production-ready
or fully stable replacement for the desktop application. Android behavior can
vary with the device, Android version, available storage, network, and system
background restrictions; incomplete or changing behavior is expected.

The current standalone implementation:

- Accepts public YouTube URLs matching `youtube.com` or `youtu.be`
- Offers **Best available**, **Up to 1080p**, **Up to 720p**, and **Up to 480p**
  choices
- Resolves video and audio streams with the embedded `yt-dlp` runtime
- Downloads the streams to the app cache, combines compatible tracks with
  Android's native `MediaMuxer`, and publishes an MP4 to Downloads
- Requires no PC, account, password, or browser cookie for this standalone
  workflow

It does not implement the desktop CLI's Instagram support, interactive format
list, audio-only workflow, subtitle workflow, playlist workflow, history, or
settings.

#### Known Android limitations

The following limitations are either documented current behavior or directly
visible in the implementation. They describe the current state, not promised
fixes:

| Area | Status | Description |
| --- | --- | --- |
| Basic downloads | Working for basic cases | Basic public YouTube downloads have been tested successfully. This does not establish reliability for large files, long videos, every format, or every device. |
| Large files | Limited | Each stream is written to the app cache before the completed MP4 is copied to Downloads. Large media therefore needs space for intermediate streams and the final file; the app performs no size or disk-space preflight. Larger downloads may be significantly slower, unreliable, or fail. No verified standalone workaround is currently documented. |
| Long videos | Limited | Long-duration downloads use the same foreground activity workflow and may take an impractical amount of time or become unreliable. There is no verified standalone workaround beyond trying a shorter or smaller download. |
| Download speed | Inconsistent | Transfers use a simple sequential `HttpURLConnection` loop with fixed timeouts and no adaptive throughput or byte-level progress reporting. Performance can vary significantly with the network, device, and source. |
| Format detection | Limited | The app does not show the source's available formats. It requests MP4 video and M4A audio through four fixed quality presets; a source without a compatible match can fail instead of opening the desktop format-selection flow. |
| Playlists | Not implemented | The embedded downloader explicitly rejects playlist metadata. Only individual public YouTube media items are supported. There is no workaround in the standalone app; use the desktop CLI for playlists. |
| Background downloads | Limited and unreliable | Downloads are started by the activity and run on its single executor. There is no foreground service, persistent notification, queued download manager, or resume queue; leaving the activity or Android reclaiming the process can interrupt the operation. |
| Storage | Basic file handling | Intermediate `.part` files are stored in the app cache and overwritten on a new attempt. The final file is written to Downloads through `MediaStore` on Android 10+, with no user-selected output directory, overwrite setting, cleanup flow, or resume support. Android storage behavior can therefore affect completion. |
| Media processing | Limited | The standalone app does not run FFmpeg or transcode. It relies on Android's native `MediaMuxer` and compatible MP4 video/audio tracks; unsupported codecs or tracks can fail rather than being converted. This is separate from the desktop CLI's FFmpeg-based processing. |
| Device compatibility | Varies | The project declares Android 10+ and ABI filters for `arm64-v8a`, `armeabi-v7a`, and `x86_64`, but behavior can still differ across Android versions, hardware, codecs, storage implementations, and system restrictions. |
| Access-restricted media | Unsupported by design | Private, login-gated, age-restricted, CAPTCHA-protected, or otherwise unavailable media can fail. The app does not provide an authentication or access-control bypass. |

These are limitations and work-in-progress areas, not a stability rating.
Users should not expect the Android APK to provide the same reliability as the
desktop CLI yet. Some functionality may not work reliably, and bugs or
incomplete behavior are expected during development.

Current verified build requirements:

- Android 10 or newer (API 29+)
- Internet access
- Android Studio Ladybug or newer for local builds
- Android SDK 35
- Java 17 and Gradle 8.9 for the repository build workflow

The latest verified experimental Android release is:

<https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.2-android>

All releases are listed at:

<https://github.com/sudopyraj/streamnest-cli/releases>

To build the debug APK, open `android-app/` in Android Studio and choose
**Build > Build APK(s)**. The repository workflow also builds it with:

```bash
cd android-app
gradle :app:assembleStandaloneDebug --no-daemon
```

The resulting APK is:

```text
android-app/app/build/outputs/apk/standalone/debug/app-standalone-debug.apk
```

## Advanced CLI

The interactive interface is recommended for normal use. The `media-dl`
command also supports one-shot downloads and maintenance commands:

```bash
# Interactive mode
media-dl

# Video downloads
media-dl "URL"
media-dl "URL" --quality 1080p
media-dl "URL" --mode best
media-dl "URL" --output ~/Videos
media-dl "URL" --max-size 50

# Audio and format inspection
media-dl "URL" --audio --format mp3
media-dl "URL" --list-formats

# Playlists and subtitles
media-dl "PLAYLIST_URL" --playlist-items 1-5,7
media-dl "URL" --subtitles en --embed-subs

# History and configuration
media-dl history --search "cats"
media-dl history --clear
media-dl config --path
media-dl config --set theme=light
media-dl config --reset

# Detailed diagnostics
media-dl --debug "URL"
```

`--mode` accepts `best`, `balanced`, or `small`. `--quality` accepts video
resolutions from `240p` through `2160p`, or audio bitrates when used with
`--audio`. Use `media-dl --help` for the complete Typer-generated help.

## Development

Clone the repository and create a development environment:

```bash
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

Run the test suite with:

```bash
python -m pytest
```

The project uses `pytest`; the test configuration is defined in
`pyproject.toml` and targets the `tests/` directory.

## Project structure

```text
streamnest-cli/
├── main.py                         # Checkout launcher and Flask entry point
├── companion.py                    # Local companion server
├── pyproject.toml                  # Package metadata, scripts, and test config
├── LICENSE
├── README.md
├── src/
│   └── media_downloader/
│       ├── cli.py                  # Interactive and one-shot CLI
│       ├── config.py               # TOML configuration
│       ├── database.py             # SQLite history storage
│       ├── downloader.py           # yt-dlp download engine
│       ├── formats.py              # Format discovery and selectors
│       ├── history.py              # History UI
│       ├── progress.py             # Progress reporting
│       ├── security.py             # URL and path validation
│       ├── ffmpeg.py               # FFmpeg detection and execution
│       ├── web.py                  # Flask web interface
│       └── platforms/              # Platform-specific helpers
├── android-app/                    # Experimental standalone Android app
└── tests/                          # Python test suite
```

## Security and privacy

StreamNest treats URLs, metadata, and filenames from external services as
untrusted input. The implementation includes:

- Exact supported-host allow-listing for YouTube and Instagram
- HTTP/HTTPS URL validation and rejection of embedded credentials and IP
  literals
- Filename sanitisation for cross-platform illegal characters and reserved
  names
- Path traversal and absolute-path checks for output files
- Filename-template validation that rejects path separators and `..`
- Controlled subprocess execution with argument lists rather than a shell
- Local-only configuration and SQLite history storage

User-controlled download input is not intentionally passed through a shell.
StreamNest does not intentionally read or store passwords, authentication
tokens, or browser cookies.

## Access-control boundaries

StreamNest does not intentionally provide functionality to:

- Access private accounts or private media
- Bypass authentication or login requirements
- Bypass CAPTCHA
- Bypass DRM
- Bypass other access controls or technical restrictions
- Obtain passwords or authentication tokens
- Use private account cookies
- Circumvent restrictions protecting private or restricted content

If a service requires authentication or another access-control mechanism,
StreamNest treats that as outside the supported scope rather than attempting a
bypass.

## Responsible use

Whether downloading particular content is permitted depends on applicable law,
copyright restrictions, content-owner permissions, and the relevant
platform/service terms. Users are responsible for their use of StreamNest and
for ensuring they have permission or another applicable legal basis to
download and use the content.

The project does not provide legal advice or guarantee that a particular use is
lawful in every jurisdiction.

## Contributing

Contributions are welcome in focused areas such as bug fixes, tests,
documentation, interface improvements, platform compatibility, accessibility,
performance, Android development, and security review.

Before making a large change, check existing issues and keep the change aligned
with the project's public-content and access-control boundaries. Run:

```bash
python -m pytest
```

Please do not add functionality intended to defeat authentication, CAPTCHA,
DRM, or other access controls.

## Bug reports

Include useful, non-sensitive diagnostic information such as:

- Operating system and Python version
- StreamNest version
- Android version and device model, when relevant
- The interface and options used
- Approximate media duration
- Whether FFmpeg is installed
- The relevant error message or redacted debug output

Never publish:

- Passwords
- Authentication tokens
- Browser cookies
- Private URLs
- Private account information
- Personal data

For a suspected security vulnerability, avoid posting sensitive exploit
details in a public issue until the maintainer has had an opportunity to
review it.

## License

StreamNest is released under the MIT License.

Copyright (c) 2026 Prince Raj

See [`LICENSE`](LICENSE) for the complete license text.

## Disclaimer

StreamNest is provided “as is”, without warranties of any kind, to the extent
permitted by applicable law. Third-party platforms can change their services,
availability, APIs, technical behavior, or terms at any time. StreamNest does
not control those services, and compatibility or successful downloads are not
guaranteed.

Users are responsible for their own use of the software and must comply with
applicable law, content-owner permissions, and relevant service terms.

## Project philosophy

StreamNest aims to keep the project:

- Open source and transparent
- Simple to understand and use
- Local-first where practical
- Friendly to beginners without hiding advanced controls
- Privacy-conscious
- Security-conscious
- Focused on responsible support for public content

The goal is a useful tool that people can inspect, run locally, and improve —
not a system for defeating platform security.

## Links

- **Repository:** <https://github.com/sudopyraj/streamnest-cli>
- **Issues:** <https://github.com/sudopyraj/streamnest-cli/issues>
- **Latest Android release:** <https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.2-android>
- **All releases:** <https://github.com/sudopyraj/streamnest-cli/releases>
