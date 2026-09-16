<div align="center">
🎬 StreamNest
A free, open-source, beginner-friendly media downloader.
License: MIT

Python 3.10+

Open Source
StreamNest provides a simple, interactive interface for downloading publicly accessible media from supported platforms. Choose an option, paste a URL, select your quality, and let StreamNest handle the rest.
Features • Installation • Usage • Interfaces • Security
</div>
⚖️ Legal and Responsible Use
> Important: StreamNest is a software tool. Whether you may download particular content depends on the content owner's permissions, applicable law, and the terms that govern the relevant service. You are responsible for how you use the software.
> 
StreamNest is provided as an open-source software project. The software itself does not determine whether a particular download is permitted. Before downloading content, make sure you have the necessary permission or other applicable legal basis to do so.
You are responsible for complying with:
 * Applicable copyright law
 * Applicable local laws and regulations
 * The terms governing the platform or service
 * Restrictions imposed by the content owner
Example: Downloading your own publicly accessible video for backup is different from downloading and redistributing someone else's copyrighted material without permission.
Do not use StreamNest to obtain or redistribute content you are not legally permitted to access or copy. The StreamNest project does not provide legal advice and does not guarantee that every use of the software is lawful in every jurisdiction.
✨ Features
StreamNest is designed to be accessible to beginners without memorizing complex command-line flags.
Supported Workflows
 * YouTube: Videos, Shorts, Playlists, and available public subtitles.
 * Instagram: Public posts and public Reels.
 * Audio Extraction: Convert media directly to audio.
 * Playlists: Download entire playlists or specify custom ranges (e.g., 1-5,7,10-12).
 * Resilience: Resume interrupted downloads safely.
Download & Quality Management
| Category | Capabilities |
|---|---|
| Quality Options | Best Quality, Balanced, Small File, Custom, Maximum File Size, or Format List. |
| Audio Formats | MP3, M4A, Opus, or Original audio format. |
| Management | Resume .part files, rich progress display, speed/ETA monitoring. |
| Configuration | Customizable download directories, concurrent download limits, and theming. |
| History | Local SQLite database for tracking, searching, and managing download history. |
📦 Requirements
 * OS: Windows, macOS, or Linux
 * Python: 3.10 or newer
 * Internet connection
 * FFmpeg: Highly recommended (required for merging video/audio, format conversion, and subtitle embedding).
🚀 Installation
StreamNest uses a Python virtual environment (.venv) to isolate its dependencies. This prevents conflicts with your system's built-in Python packages and keeps your OS clean.
<details open>
<summary><b>Linux / macOS</b></summary>
Open your terminal and run:
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install StreamNest
python -m pip install --upgrade pip
python -m pip install -e .

</details>
<details>
<summary><b>Windows PowerShell</b></summary>
Open PowerShell and run:
git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

# Create and activate a virtual environment
py -m venv .venv
.venv\Scripts\Activate.ps1

# Install StreamNest
python -m pip install --upgrade pip
python -m pip install -e .

</details>
🎬 Install FFmpeg (Recommended)
StreamNest detects FFmpeg automatically once installed on your system.
 * Ubuntu / Debian: sudo apt install ffmpeg
 * Fedora: sudo dnf install ffmpeg
 * Arch Linux: sudo pacman -S ffmpeg
 * macOS (Homebrew): brew install ffmpeg
 * Windows (WinGet): winget install Gyan.FFmpeg
🖥️ First Launch & Usage
Launch Commands
Once installed, StreamNest is designed to be easy to start. You can launch the interactive application using any of the following commands:
streamnest

or
media-dl

(Both commands launch the exact same beginner-friendly interface. You do not need to type python main.py every time if the package is installed correctly!)
If you prefer to run it directly from the source directory, you can still use:
python main.py

The Interactive Workflow
Downloading media takes just a few steps. You don't need to learn any complex commands.
 * Start StreamNest using one of the commands above.
 * Select an option from the menu (e.g., <kbd>1</kbd> for Download Media).
 * Paste a supported public URL when prompted.
 * StreamNest will validate the URL and retrieve metadata (Title, Duration, etc.).
 * Select quality and output format from the simple numbered lists.
 * The download begins with a rich progress bar.
 * View your completed file in your configured download directory!
Example Terminal Session:
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

📱 Ecosystem & Interfaces
StreamNest offers several ways to interact with the downloader depending on your needs.
Android Capabilities
StreamNest includes support for Android workflows, segmented into two distinct modes:
| Mode | PC Required? | Description |
|---|---|---|
| Android Companion | Yes | The Android device connects over a local network to StreamNest running on your PC. |
| Standalone Android (Experimental) | No | The downloader runs directly on the Android device itself. |
Note: The Standalone Android version is currently Experimental. It may have known limitations regarding performance, handling very large downloads, background downloading, and specific format detection compared to the desktop version.
Local PC Companion
You can run StreamNest as a local companion service to trigger downloads from another device.
Start the companion locally:
python companion.py

Allow LAN devices to connect:
python companion.py --host 0.0.0.0

Then open http://<computer-lan-ip>:5000 on your other device (like your phone).
> ⚠️ Security Warning: Only expose the companion service to networks you completely trust (like your home Wi-Fi). Do not expose the companion service directly to the public internet.
> 
Web Interface
StreamNest contains a lightweight local web interface. It follows the exact same public-content and URL-validation rules as the CLI.
Start the web interface:
flask --app main:app run

Then open: [http://127.0.0.1:5000](http://127.0.0.1:5000)
> Important: This interface is meant for local network use, NOT as a public centralized download service. For large or long-running downloads, the local CLI application is heavily preferred to avoid serverless timeouts, bandwidth limits, and storage constraints.
> 
<details>
<summary><b>Advanced Command Interface</b></summary>
While the interactive interface is highly recommended for beginners, StreamNest retains an advanced command-line interface for scripting and experienced power users. Run <code>streamnest --help</code> to view available programmatic flags.
</details>
🔐 Security and Privacy
StreamNest prioritizes user security and operates with a strict public-content-only scope.
The application validates supported URLs, treats remote filenames as untrusted input, and uses protected subprocess execution (avoiding dangerous shell injections).
StreamNest does NOT intentionally provide functionality to:
 * Access private accounts or bypass login requirements
 * Bypass CAPTCHAs, DRM, or other access controls
 * Obtain passwords or authentication tokens
 * Use private account cookies
 * Circumvent technical restrictions protecting private content
Data Storage
Stored Locally:
StreamNest stores your download history and configuration locally on your machine.
 * Media title, URL, platform, download status, timestamp, output path, and file size.
 * History: ~/.local/share/media-downloader/history.sqlite3
 * Config: ~/.config/media-downloader/config.toml
Not Intentionally Stored:
 * Passwords or private account credentials
 * Authentication tokens
 * Browser cookies
🛠️ Development & Contributing
Project Structure
streamnest-cli/
├── main.py            # Main interactive entry point
├── companion.py       # PC Companion service
├── streamnest/        # Core application package
├── tests/             # Test suite
├── setup.py           # Package configuration
└── README.md

Setup for Development
To work on StreamNest, ensure you set up the virtual environment as detailed in the installation section.
StreamNest welcomes contributions in areas already supported by the project (e.g., UI improvements, platform fixes for public content, test coverage).
Testing
Run the test suite to ensure your changes don't break existing functionality:
# Ensure you are in your active virtual environment
python -m unittest discover tests/

Bug Reporting
When reporting a bug on GitHub, please include terminal output, the OS you are using, and the expected behavior.
Do NOT post:
 * Passwords, cookies, or authentication tokens
 * Private URLs or personal account information
 * Any personal data
📝 Philosophy & Scope
Project Philosophy:
 * Free & Open Source
 * No built-in advertising or mandatory accounts
 * Privacy and security-conscious
 * Beginner-friendly & Local-first
 * Publicly accessible content only
Project Scope:
StreamNest intentionally focuses on publicly accessible media. The project does not aim to become a tool for defeating platform security. If a download fails because a platform requires authentication, DRM, or CAPTCHA, the appropriate behavior is to report the failure—not to attempt to bypass the restriction.
<div align="center">
<p>Released under the <a href="[https://github.com/sudopyraj/streamnest-cli/blob/main/LICENSE](https://github.com/sudopyraj/streamnest-cli/blob/main/LICENSE)">MIT License</a>.</p>
<p><a href="[https://github.com/sudopyraj/streamnest-cli](https://github.com/sudopyraj/streamnest-cli)">GitHub Repository</a></p>
</div>
