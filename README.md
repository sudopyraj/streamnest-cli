<h1 align="center">StreamNest</h1>

<p align="center">
  <strong>A beginner-friendly, open-source media downloader for publicly accessible content.</strong>
</p>

<p align="center">
  Download supported media through an interactive desktop CLI, lightweight web interface, local PC companion, or experimental standalone Android application.
</p>

<p align="center">
  <a href="https://github.com/sudopyraj/streamnest-cli">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=flat-square&logo=github" alt="GitHub Repository">
  </a>
  <a href="https://github.com/sudopyraj/streamnest-cli/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT License">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10 or newer">
  </a>
  <a href="https://github.com/sudopyraj/streamnest-cli/releases">
    <img src="https://img.shields.io/badge/Android-Experimental-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Experimental Android application">
  </a>
</p>

<p align="center">
  <a href="#installation">Installation</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#android">Android</a> ·
  <a href="#contributing">Contributing</a> ·
  <a href="https://github.com/sudopyraj/streamnest-cli/releases">Releases</a>
</p>

---

StreamNest is a free and open-source media downloader with a guided interactive interface for downloading publicly accessible media from supported platforms.

Start the application, choose an option from the menu, paste a URL, select the desired quality, and follow the prompts. No account is required, no advertising is built into StreamNest, and the project does not operate a central download server for users.

> **Important:** Whether you may download particular content depends on the content owner's permissions, applicable law, and the terms governing the relevant service. You are responsible for how you use the software.

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Launching StreamNest](#launching-streamnest)
- [Usage](#usage)
- [Audio Only](#audio-only)
- [Playlists](#playlists)
- [Resume Support](#resume-support)
- [Download History](#download-history)
- [Settings](#settings)
- [Web Interface](#web-interface)
- [Local PC Companion](#local-pc-companion)
- [Android](#android)
- [Advanced Command Interface](#advanced-command-interface)
- [Development](#development)
- [Project Structure](#project-structure)
- [Security and Privacy](#security-and-privacy)
- [Responsible Use](#responsible-use)
- [Contributing](#contributing)
- [Reporting Bugs](#reporting-bugs)
- [Development Status](#development-status)
- [License](#license)
- [Disclaimer](#disclaimer)
- [Project Philosophy](#project-philosophy)

## Features

### Guided interactive interface

StreamNest is primarily designed around a beginner-friendly terminal interface:

```text
1. Download Media
2. Audio Only
3. Download Playlist
4. Download History
5. Settings
6. Help
7. Exit
```

Normal use does not require memorizing complicated command-line flags.

### Supported workflows

- YouTube videos
- YouTube Shorts
- YouTube playlists
- Available public subtitles
- Public Instagram posts
- Public Instagram reels
- Audio extraction
- Playlist selection and ranges
- Resume support for interrupted downloads

### Quality options

Choose from:

- Best Quality
- Balanced
- Small File
- Custom
- Maximum File Size
- Format List

Playlist selections can use ranges and individual items. For example:

```text
1-5,7,10-12
```

This selects items `1, 2, 3, 4, 5, 7, 10, 11, 12`.

### Audio formats

Depending on the source and installed tools, available formats can include:

- MP3
- M4A
- Opus
- Original audio

### Download management

- Resume interrupted `.part` downloads
- Rich progress display
- Download speed
- Estimated time remaining
- File size
- SQLite download history
- Configurable download directory
- Configurable concurrency
- Configurable overwrite behavior
- Configurable filename templates

## Requirements

### Desktop

- Python 3.10 or newer
- Internet connection
- FFmpeg recommended

FFmpeg may be required for:

- Merging separate video and audio streams
- Audio conversion
- Subtitle embedding

Basic downloads may work without FFmpeg when the source provides a compatible single stream.

## Installation

### Linux and macOS

Open a terminal and run:

```bash
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

### Windows PowerShell

Open PowerShell and run:

```powershell
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

> If PowerShell prevents activation because of its execution policy, use the appropriate PowerShell execution-policy configuration for your environment or run the application with the environment's Python executable directly.

## Launching StreamNest

After installation, launch StreamNest with either command:

```bash
streamnest
```

or:

```bash
media-dl
```

When running directly from the cloned repository, use:

```bash
python main.py
```

The desktop CLI is the primary StreamNest interface.

## Usage

Start the application:

```bash
python main.py
```

Choose:

```text
1. Download Media
```

Then:

1. Paste a supported public URL.
2. StreamNest validates the URL.
3. StreamNest retrieves available metadata.
4. Review the available information.
5. Select the desired quality.
6. Select the output format when available.
7. Confirm the download.
8. Wait for the progress display to finish.
9. The completed file path will be shown at the end.

Example workflow:

```text
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
```

## Audio Only

Choose:

```text
2. Audio Only
```

Then:

1. Enter the supported public media URL.
2. Select an audio quality.
3. Select the desired output format.
4. Confirm the download.

Available formats can include:

```text
MP3
M4A
Opus
Original
```

FFmpeg may be required when conversion is necessary.

## Playlists

Choose:

```text
3. Download Playlist
```

You can download the entire playlist or select individual items.

For example:

```text
1-5,7,10-12
```

means:

```text
1, 2, 3, 4, 5, 7, 10, 11, 12
```

StreamNest uses bounded concurrency rather than creating an unlimited number of simultaneous downloads.

## Resume Support

If a download is interrupted, StreamNest can preserve its partial file.

When you start the same download again, StreamNest can offer to:

- Resume the download
- Remove the partial file and restart

This can prevent unnecessary re-downloading when a connection is interrupted.

## Download History

StreamNest maintains a local SQLite database for download history.

From **Download History**, you can:

- View previous downloads
- Search by title
- Search by URL
- Search by platform
- Clear history after confirmation

History is stored locally rather than being uploaded to a StreamNest server.

## Settings

The **Settings** menu can configure:

- Download directory
- Default video quality
- Default video container
- Default audio quality
- Default audio format
- Maximum concurrent downloads
- Overwrite behavior
- Filename template
- Terminal theme
- Reset to defaults

### Local paths

Configuration:

```text
~/.config/media-downloader/config.toml
```

History:

```text
~/.local/share/media-downloader/history.sqlite3
```

Logs:

```text
~/.local/share/media-downloader/logs/
```

## Install FFmpeg

FFmpeg is strongly recommended for the best experience.

<details>
<summary><strong>Linux</strong></summary>

Ubuntu / Debian:

```bash
sudo apt install ffmpeg
```

Fedora:

```bash
sudo dnf install ffmpeg
```

Arch Linux:

```bash
sudo pacman -S ffmpeg
```

</details>

<details>
<summary><strong>macOS</strong></summary>

With Homebrew:

```bash
brew install ffmpeg
```

</details>

<details>
<summary><strong>Windows</strong></summary>

With WinGet:

```powershell
winget install Gyan.FFmpeg
```

</details>

StreamNest attempts to detect FFmpeg automatically.

## Web Interface

StreamNest contains a lightweight web interface.

Run:

```bash
flask --app main:app run
```

Then open:

<http://127.0.0.1:5000>

The web interface follows the same public-content and URL-validation restrictions as the CLI.

> **Important:** The web interface is not intended to be a public centralized download service.

Large downloads can be unsuitable for serverless hosting because of:

- Request-duration limits
- Temporary storage limits
- Bandwidth limitations
- Platform restrictions
- Resource limitations

For large or long-running downloads, the local CLI or standalone application is preferred.

## Local PC Companion

StreamNest can also run a local companion service.

Start it with:

```bash
python companion.py
```

By default, it can be accessed from the local computer.

To allow another device on the same trusted network to connect:

```bash
python companion.py --host 0.0.0.0
```

Then open the following address on the other device:

```text
http://<computer-lan-ip>:5000
```

> **Security warning:** Only expose the companion service to networks you trust. Do not expose it directly to the public internet unless you have independently implemented appropriate authentication, encryption, and network security.

## Android

StreamNest has a separate Android implementation with two Android-related workflows.

### Android companion

The Android interface can connect to a StreamNest companion running on a computer.

```text
Android phone
      │
      │ local network
      ▼
Computer running StreamNest
      │
      ▼
Internet
```

This workflow requires:

- An Android phone
- A computer running StreamNest
- A shared local network connection

### Standalone Android application

The standalone Android application is intended to run the downloader directly on the Android device.

```text
Android application
        │
        ▼
Android device network
        │
        ▼
Internet
```

A computer or StreamNest server is not required for this standalone architecture.

### Android status: Experimental

The standalone Android application is under active development.

Basic downloads have been tested successfully, but the Android implementation may currently have limitations involving:

- Download speed
- Large files
- Long videos
- Format detection
- Device compatibility
- Media processing
- Background downloads

The APK is provided primarily for testing while these areas are improved.

The current standalone APK targets:

```text
Android 10 / API 29+
```

When installing an APK manually, Android may require permission to install applications from the relevant external source. Only install APKs from a source you trust.

### Android releases

The current Android release can be found on the project's GitHub Releases page:

<https://github.com/sudopyraj/streamnest-cli/releases>

Current experimental release:

<https://github.com/sudopyraj/streamnest-cli/releases/tag/v1.0.2-android>

The Android APK is an open-source project artifact and is not distributed through a centralized StreamNest download server.

## Advanced Command Interface

The interactive interface is recommended for normal users.

Experienced users and scripts can use the command interface:

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

These commands are optional. The normal interactive interface does not require users to remember them.

## Development

Clone the repository:

```bash
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli
```

Create the development environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

The test suite is designed to work offline and covers areas including:

- Configuration
- History
- Format selection
- Download-engine wiring
- URL validation
- Filename safety
- Utility parsing

## Project Structure

```text
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
```

## Security and Privacy

StreamNest is designed with a public-content-only scope and treats externally supplied information as untrusted.

The project includes protections such as:

- Supported-host URL allow-listing
- URL validation
- Filename sanitisation
- Path traversal protection
- Safe output-path handling
- Controlled subprocess execution
- No shell execution of user-controlled download input
- Local configuration and history storage

The application uses protected subprocess execution rather than passing user-controlled input through a shell.

### Local data

StreamNest stores download history and configuration locally.

Depending on the features you use, local data can include:

- Media title
- URL
- Platform
- Download status
- Timestamp
- Output path
- File size

StreamNest does not intentionally store:

- Passwords
- Authentication tokens
- Browser cookies
- Private account credentials

## Responsible Use

StreamNest intentionally focuses on publicly accessible media. The software itself does not determine whether a particular download is permitted.

The project does not intentionally provide functionality to:

- Access private accounts
- Bypass authentication or login requirements
- Bypass CAPTCHA
- Bypass DRM
- Bypass other access controls
- Obtain passwords or authentication tokens
- Use private account cookies
- Circumvent technical restrictions protecting private or restricted content

Before downloading content, make sure you have the necessary permission or other applicable legal basis to do so.

You are responsible for complying with:

- Applicable copyright law
- Applicable local laws and regulations
- The terms governing the platform or service
- Restrictions imposed by the content owner

For example, downloading your own publicly accessible video for backup is different from downloading and redistributing someone else's copyrighted material without permission.

Do not use StreamNest to obtain or redistribute content you are not legally permitted to access or copy.

If a download fails because the platform requires authentication, CAPTCHA verification, DRM authorization, or another access-control mechanism, do not attempt to circumvent that restriction. Report the failure instead.

The StreamNest project does not provide legal advice and does not guarantee that every use of the software is lawful in every jurisdiction.

## Contributing

StreamNest is an open-source project and contributions are welcome.

Useful contributions include:

- Bug fixes
- Tests
- Documentation
- UI improvements
- Performance profiling
- Android improvements
- Accessibility improvements
- Security reviews
- Platform compatibility fixes
- Code cleanup

Before submitting a large change, check existing issues and discussions so work is not duplicated.

Run the test suite with:

```bash
python -m pytest
```

Please keep changes focused and avoid introducing functionality that defeats authentication, CAPTCHA, DRM, or other access controls.

### Security reports

Security improvements and vulnerability reports are welcome.

If you discover a security vulnerability, avoid publicly posting sensitive exploit details in a normal issue until the project maintainer has had an opportunity to review it.

## Reporting Bugs

When reporting a bug, include as much non-sensitive information as possible:

- Operating system
- Python version
- StreamNest version
- Android version, if applicable
- Device model, if applicable
- Selected quality
- Approximate media duration
- Whether FFmpeg is installed
- Relevant error message
- Debug logs with private information removed

Do not post:

- Passwords
- Browser cookies
- Authentication tokens
- Private URLs
- Private account information
- Personal data

## Development Status

StreamNest is an actively developed open-source project.

The desktop CLI is the primary development target.

The standalone Android application is currently experimental, with ongoing work focused on:

- Download performance
- Large-file reliability
- Format detection
- Background downloading
- Android storage handling
- Media processing
- Device compatibility

The web interface and PC companion are additional interfaces rather than replacements for the core application.

## License

StreamNest is released under the MIT License.

Copyright (c) 2026 Prince Raj

See [`LICENSE`](LICENSE) for the complete license text.

The MIT License permits use, modification, and distribution subject to its terms.

## Disclaimer

StreamNest is provided “as is”, without warranties of any kind, to the extent permitted by applicable law.

The project does not guarantee:

- Availability of any particular platform
- Continued compatibility with third-party services
- Successful downloads of every public URL
- Uninterrupted operation
- Compatibility with every device
- That a particular use of the software is legally permitted

Third-party platforms can change their services, APIs, technical behavior, or terms at any time. StreamNest does not control those third-party services.

Users are responsible for their own use of the software and for ensuring that their downloads comply with applicable law, content-owner permissions, and relevant service terms.

## Project Philosophy

> **“A useful open-source tool should be simple, transparent, and respectful of its users.”**

StreamNest aims to provide:

- No built-in advertising
- No mandatory account
- Transparent source code
- Local-first operation where practical
- Beginner-friendly interfaces
- Privacy-conscious design
- Security-conscious implementation
- Responsible public-content support

The goal is not to defeat platform security. The goal is to build useful open-source software that people can understand, inspect, improve, and contribute to.

## Repository

**GitHub:** <https://github.com/sudopyraj/streamnest-cli>

If you find the project useful, consider starring the repository or contributing improvements.
