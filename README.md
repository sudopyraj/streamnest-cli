# StreamNest

**StreamNest** is a beginner-friendly, interactive terminal application for
downloading publicly accessible YouTube and Instagram media. It is designed to
feel like a small terminal app: start it once, then use numbered menus and
guided prompts instead of remembering flags or command syntax.

[**Download the Android APK**](https://github.com/sudopyraj/streamnest-cli/releases/download/v1.0.0-android/app-debug.apk)
 · [View the release](https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.0-android)

> Download only content you have permission to download. Respect platform
> terms of service and applicable copyright law.

## Highlights

- Interactive menu-driven workflow launched with one command
- YouTube videos, Shorts, playlists, subtitles, and audio extraction
- Public Instagram posts, reels, and IGTV media
- Best, balanced, small-file, custom, and file-size-aware quality choices
- MP3, M4A, Opus, or original audio
- Resume support for interrupted `.part` downloads
- Playlist selection with ranges such as `1-5,7,10-12`
- Rich progress bars with speed, ETA, and file sizes
- SQLite download history with search and safe clearing
- Guided settings for output directory, quality, format, themes, and concurrency
- URL allow-listing, filename sanitisation, path traversal protection, and no
  shell execution of user input
- Friendly errors without Python tracebacks for normal users

## What you need

- Python **3.10 or newer**
- FFmpeg is strongly recommended. It is required when StreamNest needs to
  merge separate video/audio streams, convert audio, or embed subtitles.
- Internet access for metadata lookup and downloads

## Installation

### Linux and macOS

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

## FFmpeg installation

| Operating system | Command |
| --- | --- |
| Debian/Ubuntu | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg` |
| Arch | `sudo pacman -S ffmpeg` |
| macOS with Homebrew | `brew install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg` |

StreamNest detects FFmpeg automatically and displays platform-specific
guidance if it is missing. Basic downloads may still work without it when the
source provides a compatible single stream.

## Start StreamNest

From a checkout:

```bash
python main.py
```

After installation, these commands open the same interactive application:

```bash
streamnest
# or
media-dl
```

### Web interface

StreamNest also includes a lightweight web interface for Vercel and other
WSGI hosts. Start it locally with:

```bash
flask --app main:app run
```

Open `http://127.0.0.1:5000`, paste a public YouTube or Instagram URL, inspect
the metadata, and download video or audio in the browser. The web interface
uses the same URL allow-list and public-content restrictions as the CLI. For
large or long-running downloads, the CLI remains the recommended option
because serverless hosts enforce request duration and temporary-storage limits.

### Local companion for PC and Android

For downloads that work from a user's own network, run the companion locally:

```bash
python companion.py
```

Then open `http://127.0.0.1:5000` in a PC browser and choose the browser's
**Install StreamNest** option when available. This keeps extraction and
downloads on the user's computer and avoids shared serverless IP blocks.

On Android, the responsive interface can be opened in Chrome and added to the
home screen. The Android device must be able to reach the companion service:

```bash
python companion.py --host 0.0.0.0
```

Open `http://<computer-lan-ip>:5000` on the phone. Keep the computer and phone
on the same trusted Wi-Fi network; do not expose this service directly to the
public internet. A standalone Android APK requires packaging the Python
downloader with a native runtime and is a separate release artifact.

### Android APK

The separate open-source Android companion project is in [`android-app/`](android-app/).
It provides a native Android shell for the local companion, remembers the
companion address, supports Android downloads, and does not request accounts,
passwords, or browser cookies. See
[`android-app/README.md`](android-app/README.md) for Android Studio build and
installation instructions.

The standalone Android APK can be downloaded directly from the
[latest StreamNest Android release](https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.0-android).
It requires Android 10/API 29 or newer. Enable installation from unknown
sources when installing the open-source APK outside Google Play.

The main menu provides:

```text
1. Download Media
2. Audio Only
3. Download Playlist
4. Download History
5. Settings
6. Help
7. Exit
```

You do not need to enter a URL, path, ID, quality flag, or complex command
before starting. Select a menu item and follow the prompts.

## Complete download workflow

### Download a video or public Instagram media item

1. Start StreamNest with `python main.py`.
2. Choose **Download Media**.
3. Paste the YouTube, YouTube Shorts, or public Instagram URL.
4. StreamNest validates the URL and retrieves its metadata.
5. Review the title, platform, duration, uploader, and available formats.
6. Choose a download mode:
   - **Best Quality** — highest available quality.
   - **Balanced** — up to 1080p with a practical file size.
   - **Small File** — up to 480p for mobile or limited storage.
   - **Custom** — choose resolution, FPS, and container.
   - **Maximum file size** — show only formats that fit the limit.
   - **Choose from format list** — inspect source-provided formats.
7. Choose MP4, WebM, or the original container when applicable.
8. For YouTube, optionally select available subtitles and choose whether to
   embed them.
9. StreamNest checks disk space, shows progress, and downloads the media.
10. The completion screen shows the saved path and file size. The download is
    recorded in history.

### Download audio only

1. Choose **Audio Only**.
2. Enter the media URL.
3. Choose an audio bitrate cap: best, 320, 256, 192, or 128 kbps.
4. Choose MP3, M4A, Opus, or **Original**.
5. Confirm the source/output quality information.
6. StreamNest downloads and converts only when FFmpeg is needed.

### Download a playlist

1. Choose **Download Playlist**.
2. Paste a YouTube playlist URL.
3. Choose **Download all** or **Select videos**.
4. If selecting videos, enter numbers or ranges such as `1-5,7,10-12`.
5. Choose a shared quality mode and output container.
6. StreamNest downloads with bounded concurrency and displays overall progress.

Interrupted downloads keep their partial files. When the same item is started
again, StreamNest offers to resume or remove the partial files and start over.

## History and settings

### Download history

Choose **Download History** to:

- View recent downloads in a readable table
- Search by title, URL, or platform
- Clear all history after confirmation

Only non-sensitive metadata is stored. StreamNest never reads or stores
cookies, passwords, authentication tokens, or private account credentials.

### Settings

The interactive Settings menu can edit:

- Download directory
- Default video quality and container
- Default audio quality and format
- Maximum concurrent downloads
- Whether existing files may be overwritten
- Safe filename template
- Terminal theme
- Reset all settings to defaults

Configuration is stored at:

```text
~/.config/media-downloader/config.toml
```

Runtime data is stored at:

```text
~/.local/share/media-downloader/history.sqlite3
~/.local/share/media-downloader/logs/
```

## Advanced command interface

The interactive interface is recommended. The existing direct command
interface remains available for scripts and experienced users:

```bash
media-dl "URL"
media-dl "URL" --quality 1080p
media-dl "URL" --mode best
media-dl "URL" --audio --format mp3
media-dl "URL" --list-formats
media-dl "URL" --output ~/Videos
media-dl "PLAYLIST_URL" --playlist-items 1-5,7
media-dl history --search "cats"
media-dl config --reset
media-dl --debug "URL"
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

The test suite is offline and covers configuration, history, format selection,
download-engine wiring, URL validation, filename safety, and utility parsing.

## Project structure

```text
streamnest-cli/
├── main.py                         # python main.py launcher
├── pyproject.toml                  # package metadata and dependencies
├── LICENSE                         # MIT open-source license
├── src/media_downloader/
│   ├── cli.py                      # interactive UI and command compatibility
│   ├── config.py                   # TOML configuration and themes
│   ├── database.py                 # SQLite history storage
│   ├── downloader.py               # yt-dlp download engine
│   ├── formats.py                  # format discovery and selectors
│   ├── history.py                  # history menus and tables
│   ├── progress.py                 # Rich progress reporting
│   ├── security.py                 # URL and path safety
│   ├── ffmpeg.py                   # FFmpeg detection
│   ├── web.py                      # Vercel-compatible web UI and API
│   └── platforms/                  # YouTube and Instagram helpers
└── tests/                          # offline automated tests
```

## Safety and scope

StreamNest supports only public media from allow-listed YouTube and Instagram
hostnames. It does not bypass private accounts, login gates, CAPTCHA, DRM, or
other access controls. Remote filenames are treated as untrusted input, output
paths are checked for safety, and FFmpeg is invoked without a shell.

## License

StreamNest is released under the **MIT License**. See [LICENSE](LICENSE).
