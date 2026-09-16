StreamNest

StreamNest is a free and open-source media downloader with a beginner-friendly interactive interface for downloading publicly accessible media from supported platforms.

It is designed to be simple: start the application, choose an option from a menu, paste a URL, select the desired quality, and follow the prompts.

No account is required. No advertising is built into StreamNest. The project does not operate a central download server for users.

«Important: StreamNest is a software tool. Whether you may download particular content depends on the content owner's permissions, applicable law, and the terms that govern the relevant service. You are responsible for how you use the software.»

---

✨ Features

Simple interactive interface

StreamNest is primarily designed around a guided terminal interface.

1. Download Media
2. Audio Only
3. Download Playlist
4. Download History
5. Settings
6. Help
7. Exit

You don't need to remember complicated command-line flags for normal use.

Supported media workflows

- YouTube videos
- YouTube Shorts
- YouTube playlists
- Available public subtitles
- Public Instagram posts
- Public Instagram reels
- Audio extraction
- Playlist selection and ranges
- Resume support for interrupted downloads

Quality options

Choose from:

- Best Quality
- Balanced
- Small File
- Custom
- Maximum File Size
- Format List

For example:

1-5,7,10-12

can be used to select specific playlist items.

Audio formats

Depending on the source and installed tools:

- MP3
- M4A
- Opus
- Original audio

Download management

- Resume interrupted ".part" downloads
- Rich progress display
- Download speed
- ETA
- File size
- SQLite download history
- Configurable download directory
- Configurable concurrency

---

🔐 Safety and Privacy

StreamNest is designed with a public-content-only scope.

The project does not intentionally provide functionality to:

- access private accounts
- bypass login requirements
- bypass CAPTCHA
- bypass DRM
- bypass other access controls
- obtain passwords
- obtain authentication tokens
- use private account cookies
- circumvent technical restrictions protecting private or restricted content

StreamNest also validates supported URLs and treats remote filenames as untrusted input.

The application uses protected subprocess execution rather than passing user-controlled input through a shell.

Local data

StreamNest stores download history and configuration locally.

Depending on the features you use, local data can include information such as:

- media title
- URL
- platform
- download status
- timestamp
- output path
- file size

StreamNest does not intentionally store:

- passwords
- authentication tokens
- browser cookies
- private account credentials

---

⚖️ Legal and Responsible Use

StreamNest is provided as an open-source software project.

The software itself does not determine whether a particular download is permitted.

Before downloading content, make sure you have the necessary permission or other applicable legal basis to do so.

You are responsible for complying with:

- applicable copyright law
- applicable local laws and regulations
- the terms governing the platform or service
- restrictions imposed by the content owner

For example, downloading your own publicly accessible video for backup is different from downloading and redistributing someone else's copyrighted material without permission.

Do not use StreamNest to obtain or redistribute content you are not legally permitted to access or copy.

The StreamNest project does not provide legal advice and does not guarantee that every use of the software is lawful in every jurisdiction.

---

🚫 Project Scope

StreamNest intentionally focuses on publicly accessible media.

The project does not aim to become a tool for defeating platform security or access controls.

If a platform requires authentication, CAPTCHA verification, DRM authorization, or another access-control mechanism, StreamNest should not be used to circumvent that mechanism.

If a download fails because the platform requires something outside StreamNest's supported scope, the appropriate behavior is to report the failure rather than attempt to bypass the restriction.

---

📦 Requirements

Desktop

- Python 3.10 or newer
- Internet connection
- FFmpeg recommended

FFmpeg may be required for:

- merging separate video and audio streams
- audio conversion
- subtitle embedding

Basic downloads may work without FFmpeg when the source provides a compatible single stream.

---

🚀 Installation

Linux / macOS

Open a terminal and run:

git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .

Then start StreamNest:

python main.py

If the package is installed with its command entry points, you can also use:

streamnest

or:

media-dl

---

Windows PowerShell

Open PowerShell:

git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .

Start the application:

python main.py

Or:

streamnest

---

🎬 Install FFmpeg

FFmpeg is strongly recommended.

Ubuntu / Debian

sudo apt install ffmpeg

Fedora

sudo dnf install ffmpeg

Arch Linux

sudo pacman -S ffmpeg

macOS

With Homebrew:

brew install ffmpeg

Windows

With WinGet:

winget install Gyan.FFmpeg

StreamNest attempts to detect FFmpeg automatically.

---

🖥️ Using StreamNest

Start the application:

python main.py

You will see the interactive menu.

Choose:

1. Download Media

Then:

1. Paste a supported public URL.
2. StreamNest validates the URL.
3. StreamNest retrieves available metadata.
4. Review the available information.
5. Select the desired quality.
6. Select the output format when available.
7. Confirm the download.
8. Wait for the progress display to finish.
9. The completed file will be shown at the end.

Example workflow:

StreamNest

1. Download Media
2. Audio Only
3. Download Playlist
4. Download History
5. Settings
6. Help
7. Exit

Select an option: 1

Enter media URL:
> https://example.com/...

Checking URL...
Retrieving media information...

Title: Example Video
Duration: 05:42

Choose quality:
1. Best Quality
2. Balanced
3. Small File
4. Custom
5. Maximum File Size
6. Choose from format list

Select: 2

---

🎵 Audio Only

Choose:

2. Audio Only

Then:

1. Enter the supported public media URL.
2. Select an audio quality.
3. Select the desired output format.
4. Confirm the download.

Available formats can include:

MP3
M4A
Opus
Original

FFmpeg may be required when conversion is necessary.

---

📋 Playlists

Choose:

3. Download Playlist

You can download the entire playlist or select individual items.

Example:

1-5,7,10-12

means:

1, 2, 3, 4, 5, 7, 10, 11, 12

StreamNest uses bounded concurrency rather than creating an unlimited number of simultaneous downloads.

---

🔄 Resume Interrupted Downloads

If a download is interrupted, StreamNest can preserve its partial file.

When you start the same download again, StreamNest can offer to:

Resume
Remove partial file and restart

This can prevent unnecessary re-downloading when a connection is interrupted.

---

📜 Download History

StreamNest maintains a local SQLite database for download history.

From:

Download History

you can:

- view previous downloads
- search by title
- search by URL
- search by platform
- clear history after confirmation

History is stored locally rather than being uploaded to a StreamNest server.

---

⚙️ Settings

The Settings menu can configure:

- download directory
- default video quality
- default video container
- default audio quality
- default audio format
- maximum concurrent downloads
- overwrite behavior
- filename template
- terminal theme
- reset to defaults

Configuration:

~/.config/media-downloader/config.toml

History:

~/.local/share/media-downloader/history.sqlite3

Logs:

~/.local/share/media-downloader/logs/

---

🌐 Web Interface

StreamNest also contains a lightweight web interface.

Run:

flask --app main:app run

Then open:

http://127.0.0.1:5000

The web interface follows the same public-content and URL-validation restrictions as the CLI.

Important

The web interface is not intended to be a public centralized download service.

Large downloads can be unsuitable for serverless hosting because of:

- request-duration limits
- temporary storage limits
- bandwidth limitations
- platform restrictions
- resource limitations

For large or long-running downloads, the local CLI or standalone application is preferred.

---

🖥️ Local PC Companion

StreamNest can also run a local companion service.

Start it with:

python companion.py

By default, it can be accessed from the local computer.

To allow another device on the same trusted network to connect:

python companion.py --host 0.0.0.0

Then open:

http://<computer-lan-ip>:5000

on the other device.

Security warning

Only expose the companion service to networks you trust.

Do not expose the companion service directly to the public internet unless you have independently implemented appropriate authentication, encryption, and network security.

---

📱 Android

StreamNest has a separate Android implementation.

The project currently has two Android-related workflows:

Android companion

The Android interface can connect to a StreamNest companion running on a computer.

This requires:

Android phone
      │
      │ local network
      ▼
Computer running StreamNest
      │
      ▼
Internet

Standalone Android application

The standalone Android application is intended to run the downloader directly on the Android device:

Android application
        │
        ▼
Android device network
        │
        ▼
Internet

A computer or StreamNest server is not required for the standalone architecture.

Android status

Experimental

The standalone Android application is under active development.

Basic downloads have been tested successfully, but the Android implementation may currently have limitations involving:

- download speed
- large files
- long videos
- format detection
- device compatibility
- media processing
- background downloads

The APK is provided primarily for testing while these areas are improved.

Android requirements

The current standalone APK targets:

Android 10 / API 29+

When installing an APK manually, Android may require permission to install applications from the relevant external source.

Only install APKs from a source you trust.

---

📥 Android APK

The current Android release can be found on the project's GitHub Releases page.

Android releases:

https://github.com/sudopyraj/streamnest-cli/releases

Current experimental release:

https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.2-android

The Android APK is an open-source project artifact and is not distributed through a centralized StreamNest download server.

---

💻 Advanced Command Interface

The interactive interface is recommended for normal users.

Experienced users and scripts can use the command interface:

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

These commands are optional. The normal interactive interface does not require users to remember them.

---

🛠️ Development

Clone the repository:

git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

Create the development environment:

python -m venv .venv
source .venv/bin/activate

Install development dependencies:

python -m pip install -e ".[dev]"

Run tests:

python -m pytest

The test suite is designed to work offline and covers areas including:

- configuration
- history
- format selection
- download-engine wiring
- URL validation
- filename safety
- utility parsing

---

🗂️ Project Structure

streamnest-cli/
├── main.py
├── companion.py
├── pyproject.toml
├── LICENSE
├── README.md
│
├── src/
│   └── media_downloader/
│       ├── cli.py
│       ├── config.py
│       ├── database.py
│       ├── downloader.py
│       ├── formats.py
│       ├── history.py
│       ├── progress.py
│       ├── security.py
│       ├── ffmpeg.py
│       ├── web.py
│       └── platforms/
│
├── android-app/
│   └── README.md
│
└── tests/

---

🔒 Security Design

StreamNest treats externally supplied information as untrusted.

The project includes protections such as:

- supported-host URL allow-listing
- URL validation
- filename sanitisation
- path traversal protection
- safe output-path handling
- controlled subprocess execution
- no shell execution of user-controlled download input
- local configuration and history storage

Security improvements and vulnerability reports are welcome.

If you discover a security vulnerability, please avoid publicly posting sensitive exploit details in a normal issue until the project maintainer has had an opportunity to review it.

---

🤝 Contributing

StreamNest is an open-source project and contributions are welcome.

Useful contributions include:

- bug fixes
- tests
- documentation
- UI improvements
- performance profiling
- Android improvements
- accessibility improvements
- security reviews
- platform compatibility fixes
- code cleanup

Before submitting a large change, please check existing issues and discussions so work isn't duplicated.

For development:

python -m pytest

Please keep changes focused and avoid introducing functionality that defeats authentication, CAPTCHA, DRM, or other access controls.

---

🐛 Reporting Bugs

When reporting a bug, include as much non-sensitive information as possible:

- operating system
- Python version
- StreamNest version
- Android version, if applicable
- device model, if applicable
- selected quality
- approximate media duration
- whether FFmpeg is installed
- relevant error message
- debug logs with private information removed

Do not post:

- passwords
- browser cookies
- authentication tokens
- private URLs
- private account information
- personal data

---

📌 Current Development Status

StreamNest is an actively developed open-source project.

The desktop CLI is the primary development target.

The Android standalone application is currently experimental, with ongoing work focused on:

- download performance
- large-file reliability
- format detection
- background downloading
- Android storage handling
- media processing
- device compatibility

The web interface and PC companion are additional interfaces rather than replacements for the core application.

---

📜 License

StreamNest is released under the MIT License.

Copyright (c) 2026 Prince Raj

See ""LICENSE"" (LICENSE) for the complete license text.

The MIT License permits use, modification, and distribution subject to its terms.

---

⚠️ Disclaimer

StreamNest is provided "as is", without warranties of any kind, to the extent permitted by applicable law.

The project does not guarantee:

- availability of any particular platform
- continued compatibility with third-party services
- successful downloads of every public URL
- uninterrupted operation
- compatibility with every device
- that a particular use of the software is legally permitted

Third-party platforms can change their services, APIs, technical behavior, or terms at any time.

StreamNest does not control those third-party services.

Users are responsible for their own use of the software and for ensuring that their downloads comply with applicable law, content-owner permissions, and relevant service terms.

---

🌱 Project Philosophy

StreamNest is built around a simple idea:

«A useful open-source tool should be simple, transparent, and respectful of its users.»

The project aims to provide:

- no built-in advertising
- no mandatory account
- transparent source code
- local-first operation where practical
- beginner-friendly interfaces
- privacy-conscious design
- security-conscious implementation
- responsible public-content support

The goal is not to defeat platform security.

The goal is to build a useful piece of open-source software that people can understand, inspect, improve, and contribute to.

---

⭐ Repository

GitHub:
https://github.com/sudopyraj/streamnest-cli

If you find the project useful, consider starring the repository or contributing improvements.

---