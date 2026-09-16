
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamNest - Media Downloader</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --border-color: #30363d;
            --code-bg: #161b22;
            --warning-bg: #3b2e04;
            --warning-border: #d29922;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        h1, h2, h3 {
            color: #ffffff;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.3em;
        }

        h1 {
            text-align: center;
            border-bottom: none;
            font-size: 2.5em;
        }

        p {
            margin-bottom: 1em;
        }

        a {
            color: var(--accent-color);
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        .important-note {
            background-color: var(--warning-bg);
            border-left: 4px solid var(--warning-border);
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 6px 6px 0;
        }

        pre {
            background-color: var(--code-bg);
            border: 1px solid var(--border-color);
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }

        code {
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            background-color: rgba(110, 118, 129, 0.4);
            padding: 0.2em 0.4em;
            border-radius: 6px;
            font-size: 85%;
        }

        pre code {
            background-color: transparent;
            padding: 0;
        }

        ul, ol {
            padding-left: 2em;
            margin-bottom: 1em;
        }

        .emoji-header {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .tree {
            line-height: 1.2;
            color: #8b949e;
        }
    </style>
</head>
<body>

    <h1>StreamNest</h1>
    
    <p><strong>StreamNest</strong> is a free and open-source media downloader with a beginner-friendly interactive interface for downloading publicly accessible media from supported platforms.</p>
    
    <p>It is designed to be simple: start the application, choose an option from a menu, paste a URL, select the desired quality, and follow the prompts.</p>
    
    <p>No account is required. No advertising is built into StreamNest. The project does not operate a central download server for users.</p>

    <div class="important-note">
        <strong>«Important:</strong> StreamNest is a software tool. Whether you may download particular content depends on the content owner's permissions, applicable law, and the terms that govern the relevant service. You are responsible for how you use the software.<strong>»</strong>
    </div>

    <hr style="border: 1px solid var(--border-color); margin: 2em 0;">

    <h2 class="emoji-header">✨ Features</h2>
    
    <h3>Simple interactive interface</h3>
    <p>StreamNest is primarily designed around a guided terminal interface.</p>
    <pre><code>1. Download Media
2. Audio Only
3. Download Playlist
4. Download History
5. Settings
6. Help
7. Exit</code></pre>
    <p>You don't need to remember complicated command-line flags for normal use.</p>

    <h3>Supported media workflows</h3>
    <ul>
        <li>YouTube videos</li>
        <li>YouTube Shorts</li>
        <li>YouTube playlists</li>
        <li>Available public subtitles</li>
        <li>Public Instagram posts</li>
        <li>Public Instagram reels</li>
        <li>Audio extraction</li>
        <li>Playlist selection and ranges</li>
        <li>Resume support for interrupted downloads</li>
    </ul>

    <h3>Quality options</h3>
    <p>Choose from: Best Quality, Balanced, Small File, Custom, Maximum File Size, Format List.</p>
    <p>For example: <code>1-5,7,10-12</code> can be used to select specific playlist items.</p>

    <h3>Audio formats & Download Management</h3>
    <ul>
        <li>Formats: MP3, M4A, Opus, Original audio</li>
        <li>Resume interrupted <code>.part</code> downloads</li>
        <li>Rich progress display (Download speed, ETA, File size)</li>
        <li>SQLite download history</li>
        <li>Configurable download directory & concurrency</li>
    </ul>

    <h2 class="emoji-header">🔐 Safety and Privacy</h2>
    <p>StreamNest is designed with a public-content-only scope. The project does not intentionally provide functionality to:</p>
    <ul>
        <li>access private accounts</li>
        <li>bypass login requirements, CAPTCHA, or DRM</li>
        <li>obtain passwords or authentication tokens</li>
        <li>use private account cookies</li>
        <li>circumvent technical restrictions protecting private or restricted content</li>
    </ul>
    <p>The application uses protected subprocess execution rather than passing user-controlled input through a shell. It stores download history and configuration locally. StreamNest does not intentionally store private credentials.</p>

    <h2 class="emoji-header">⚖️ Legal and Responsible Use</h2>
    <p>StreamNest is provided as an open-source software project. The software itself does not determine whether a particular download is permitted.</p>
    <p>Before downloading content, make sure you have the necessary permission or other applicable legal basis to do so. You are responsible for complying with applicable copyright law, local regulations, and terms of service.</p>

    <h2 class="emoji-header">🚫 Project Scope</h2>
    <p>StreamNest intentionally focuses on publicly accessible media. It does not aim to become a tool for defeating platform security. If a download fails because the platform requires authentication or CAPTCHA, the appropriate behavior is to report the failure rather than attempt to bypass the restriction.</p>

    <h2 class="emoji-header">📦 Requirements</h2>
    <ul>
        <li>Desktop: Python 3.10 or newer</li>
        <li>Internet connection</li>
        <li><strong>FFmpeg recommended</strong> (for merging streams, audio conversion, and subtitles)</li>
    </ul>

    <h2 class="emoji-header">🚀 Installation</h2>
    
    <h3>Linux / macOS</h3>
    <pre><code>git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .

python main.py</code></pre>

    <h3>Windows PowerShell</h3>
    <pre><code>git clone https://github.com/sudopyraj/streamnest-cli.git
cd streamnest-cli

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .

python main.py</code></pre>

    <h2 class="emoji-header">🎬 Install FFmpeg</h2>
    <ul>
        <li><strong>Ubuntu / Debian:</strong> <code>sudo apt install ffmpeg</code></li>
        <li><strong>Fedora:</strong> <code>sudo dnf install ffmpeg</code></li>
        <li><strong>Arch Linux:</strong> <code>sudo pacman -S ffmpeg</code></li>
        <li><strong>macOS:</strong> <code>brew install ffmpeg</code></li>
        <li><strong>Windows:</strong> <code>winget install Gyan.FFmpeg</code></li>
    </ul>

    <h2 class="emoji-header">🌐 Web Interface & Companions</h2>
    <p>StreamNest contains a lightweight web interface. Run: <code>flask --app main:app run</code></p>
    <p>StreamNest can also run a local companion service: <code>python companion.py</code>. Only expose this to networks you trust.</p>

    <h2 class="emoji-header">📱 Android</h2>
    <p>StreamNest has an experimental standalone Android application (Android 10 / API 29+). You can find the latest APK on the <a href="https://github.com/sudopyraj/streamnest-cli/releases">GitHub Releases page</a>.</p>

    <h2 class="emoji-header">🗂️ Project Structure</h2>
    <pre class="tree"><code>streamnest-cli/
├── main.py
├── companion.py
├── pyproject.toml
├── LICENSE
├── README.md
│
├── src/
│   └── media_downloader/
│       ├── cli.py
│       └── ...
└── tests/</code></pre>

    <h2 class="emoji-header">🤝 Contributing</h2>
    <p>StreamNest is an open-source project and contributions are welcome. Please keep changes focused and avoid introducing functionality that defeats authentication, CAPTCHA, DRM, or other access controls.</p>

    <h2 class="emoji-header">📜 License</h2>
    <p>StreamNest is released under the MIT License. Copyright (c) 2026 Prince Raj. See <code>LICENSE</code> for the complete text.</p>

    <hr style="border: 1px solid var(--border-color); margin: 2em 0;">
    
    <h2 class="emoji-header">🌱 Project Philosophy</h2>
    <p align="center"><em>«A useful open-source tool should be simple, transparent, and respectful of its users.»</em></p>
    
    <p><strong>GitHub Repository:</strong> <a href="https://github.com/sudopyraj/streamnest-cli">https://github.com/sudopyraj/streamnest-cli</a></p>

</body>
</html>

Option 2: GitHub-Optimized README.md (Highly Recommended)
Copy and paste this directly into your README.md file on GitHub. It uses a mix of Markdown and GitHub-supported HTML to look fantastic on the repository page.
<h1 align="center">StreamNest</h1>

<p align="center">
  <em>A free and open-source media downloader with a beginner-friendly interactive interface for downloading publicly accessible media from supported platforms.</em>
</p>

<p align="center">
  <a href="https://github.com/sudopyraj/streamnest-cli"><strong>View Repository</strong></a> ·
  <a href="#-installation"><strong>Install</strong></a> ·
  <a href="#-android"><strong>Android App</strong></a>
</p>

---

It is designed to be simple: start the application, choose an option from a menu, paste a URL, select the desired quality, and follow the prompts. No account is required. No advertising is built into StreamNest. The project does not operate a central download server for users.

> **Important:** StreamNest is a software tool. Whether you may download particular content depends on the content owner's permissions, applicable law, and the terms that govern the relevant service. You are responsible for how you use the software.

## ✨ Features

### Simple interactive interface
StreamNest is primarily designed around a guided terminal interface. You don't need to remember complicated command-line flags for normal use.

```text
1. Download Media
2. Audio Only
3. Download Playlist
4. Download History
5. Settings
6. Help
7. Exit

<details>
<summary><strong>Supported Media Workflows & Quality Options (Click to expand)</strong></summary>
 * YouTube videos, Shorts, and playlists
 * Available public subtitles
 * Public Instagram posts and reels
 * Audio extraction
 * Playlist selection and ranges (e.g., 1-5,7,10-12)
 * Resume support for interrupted downloads
Quality Options:
Best Quality, Balanced, Small File, Custom, Maximum File Size, Format List.
</details>
🔐 Safety and Privacy
StreamNest is designed with a public-content-only scope.
The project does not intentionally provide functionality to:
 * Access private accounts
 * Bypass login requirements, CAPTCHA, or DRM
 * Obtain passwords or authentication tokens
 * Circumvent technical restrictions protecting private content
Local data (history, config) is stored on your machine. StreamNest does not store passwords or private credentials.
📦 Requirements
 * Desktop: Python 3.10 or newer
 * Internet connection
 * FFmpeg recommended (Required for merging video/audio streams and embedding subtitles).
🚀 Installation
Linux / macOS
git clone [https://github.com/sudopyraj/streamnest-cli.git](https://github.com/sudopyraj/streamnest-cli.git)
cd streamnest-cli

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .

# Start StreamNest
python main.py

Windows PowerShell
git clone [https://github.com/sudopyraj/streamnest-cli.git](https://github.com/sudopyraj/streamnest-cli.git)
cd streamnest-cli

py -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .

# Start StreamNest
python main.py

🎬 Install FFmpeg
FFmpeg is strongly recommended for the best experience.
 * Ubuntu/Debian: sudo apt install ffmpeg
 * macOS (Homebrew): brew install ffmpeg
 * Windows (WinGet): winget install Gyan.FFmpeg
 * Arch Linux: sudo pacman -S ffmpeg
🌐 Web Interface & PC Companion
StreamNest contains a lightweight web interface:
flask --app main:app run

Open http://127.0.0.1:5000 in your browser.
You can also run a local companion service (python companion.py). Security warning: Only expose the companion service to networks you trust.
📱 Android (Experimental)
StreamNest has a standalone Android application under active development targeting Android 10 (API 29+).
 * Download the current experimental APK release here.
💻 Advanced Command Interface
Experienced users can bypass the interactive menu:
media-dl "URL" --quality 1080p
media-dl "URL" --audio --format mp3
media-dl "PLAYLIST_URL" --playlist-items 1-5,7

🤝 Contributing
Contributions are welcome! Please keep changes focused and avoid introducing functionality that defeats authentication, CAPTCHA, DRM, or other access controls.
# Setup dev environment
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest

📜 License & Legal
MIT License - Copyright (c) 2026 Prince Raj.
StreamNest is provided "as is". The project does not guarantee availability of any particular platform or that a particular use of the software is legally permitted. Users are responsible for ensuring that their downloads comply with applicable law.
<p align="center">
<em>«A useful open-source tool should be simple, transparent, and respectful of its users.»</em>
</p>

