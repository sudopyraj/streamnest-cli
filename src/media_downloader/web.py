"""Small web interface for StreamNest.

The Flask app is intentionally separate from the Typer CLI.  This keeps the
terminal entrypoints unchanged while exposing a WSGI-compatible entrypoint for
Vercel and other Python hosts.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template_string, request, send_file
from rich.console import Console

from .config import Config
from .downloader import DownloadError, MediaDownloader, is_playlist
from .security import SecurityError, sanitize_filename

app = Flask(__name__)

_VIDEO_SELECTORS = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
}
_AUDIO_FORMATS = {"original", "mp3", "m4a", "opus"}

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StreamNest — Save the good stuff</title>
  <style>
    :root { color-scheme: dark; --bg:#0b1020; --panel:#121a2d; --line:#263453;
      --text:#f5f7ff; --muted:#9aa8c5; --accent:#7c6cff; --accent2:#35d0ba; }
    * { box-sizing:border-box } body { margin:0; min-height:100vh; color:var(--text);
      font:16px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;
      background:radial-gradient(circle at 15% 0,#25205d 0,transparent 40%),var(--bg); }
    .wrap { width:min(1050px,calc(100% - 40px)); margin:auto }
    nav { display:flex; justify-content:space-between; align-items:center; padding:28px 0 }
    .brand { font-weight:800; letter-spacing:-.04em; font-size:1.2rem }
    .brand span { color:var(--accent2) } .pill { color:var(--muted); font-size:.85rem }
    main { padding:52px 0 100px; max-width:760px; margin:auto }
    .eyebrow { color:var(--accent2); font-weight:700; font-size:.78rem; letter-spacing:.14em;
      text-transform:uppercase } h1 { font-size:clamp(2.5rem,7vw,5.2rem); line-height:.98;
      letter-spacing:-.07em; margin:16px 0 20px; max-width:700px }
    .lede { color:var(--muted); font-size:1.1rem; max-width:600px; margin-bottom:34px }
    .card { background:color-mix(in srgb,var(--panel) 92%,transparent); border:1px solid var(--line);
      border-radius:24px; padding:10px; box-shadow:0 24px 70px #0005 }
    form { display:flex; gap:10px } input,select,button { border:0; border-radius:16px;
      padding:15px 17px; font:inherit } input { min-width:0; flex:1; color:var(--text);
      background:#1b2742; outline:1px solid transparent } input:focus { outline:2px solid var(--accent) }
    button { cursor:pointer; color:white; background:linear-gradient(135deg,var(--accent),#a05cff);
      font-weight:750; transition:transform .2s,filter .2s } button:hover { transform:translateY(-2px);
      filter:brightness(1.12) } button:disabled { opacity:.55; cursor:wait; transform:none }
    #status { color:var(--muted); min-height:28px; padding:14px 8px 4px }
    #result { display:none; margin-top:18px; padding:22px; border-radius:18px; background:#18233c }
    .meta { display:flex; gap:16px; align-items:center } .thumb { width:120px; height:75px;
      object-fit:cover; border-radius:10px; background:#283657 } h2 { margin:0 0 5px; font-size:1.15rem }
    .muted { color:var(--muted); font-size:.9rem } .controls { display:flex; gap:10px; margin-top:20px }
    select { flex:1; color:var(--text); background:#263657; cursor:pointer }
    .note { margin-top:24px; color:var(--muted); font-size:.86rem } .note a { color:var(--text) }
    @media(max-width:600px) { .wrap { width:min(100% - 24px,1050px) } main { padding-top:35px }
      form,.controls { flex-direction:column } button,select { width:100% } .meta { align-items:flex-start }
      .thumb { width:90px; height:60px } }
  </style>
</head>
<body><div class="wrap"><nav><div class="brand">stream<span>nest</span></div><div class="pill">YouTube + Instagram</div></nav>
<main><div class="eyebrow">Simple. Private. Focused.</div><h1>Keep the moments that matter.</h1>
<p class="lede">Paste a public YouTube or Instagram link. StreamNest will find the best version and prepare it for you.</p>
<section class="card"><form id="lookup"><input id="url" type="url" required placeholder="Paste a YouTube or Instagram URL…" autocomplete="off"><button id="inspect">Inspect link</button></form>
<div id="status"></div><div id="result"><div class="meta"><img id="thumb" class="thumb" alt="" hidden><div><h2 id="title"></h2><div id="details" class="muted"></div></div></div>
<div class="controls"><select id="kind"><option value="video">Video</option><option value="audio">Audio only</option></select><select id="quality"><option value="best">Best quality</option><option value="1080p">Up to 1080p</option><option value="720p">Up to 720p</option><option value="480p">Small file</option></select><select id="format"><option value="mp4">MP4</option><option value="webm">WebM</option></select><button id="download">Download</button></div></div></section>
<p class="note">Only public media is supported. Please download content you have permission to use. Prefer the terminal? Run <a href="https://github.com/sudopyraj/streamnest-cli">StreamNest CLI</a>.</p>
</main></div>
<script>
const $=id=>document.getElementById(id), form=$('lookup'), result=$('result');
let inspected=false;
form.addEventListener('submit',async e=>{e.preventDefault(); $('inspect').disabled=true; $('status').textContent='Looking up media…'; result.style.display='none';
  try { const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:$('url').value})}); const d=await r.json(); if(!r.ok) throw Error(d.error||'Could not inspect that link');
    $('title').textContent=d.title||'Untitled media'; $('details').textContent=[d.platform,d.duration].filter(Boolean).join(' · ');
    if(d.thumbnail){$('thumb').src=d.thumbnail;$('thumb').hidden=false} result.style.display='block'; inspected=true; $('status').textContent='Ready when you are.';
  } catch(err){$('status').textContent=err.message; } finally {$('inspect').disabled=false}
});
$('kind').addEventListener('change',e=>{const audio=e.target.value==='audio'; $('quality').style.display=audio?'none':''; $('format').innerHTML=audio?'<option value="mp3">MP3</option><option value="m4a">M4A</option><option value="opus">Opus</option><option value="original">Original</option>':'<option value="mp4">MP4</option><option value="webm">WebM</option>';});
$('download').addEventListener('click',async()=>{if(!inspected)return; $('download').disabled=true; $('status').textContent='Preparing your download…';
  try { const r=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:$('url').value,kind:$('kind').value,quality:$('quality').value,format:$('format').value})}); if(!r.ok){const d=await r.json();throw Error(d.error||'Download failed')} const blob=await r.blob(), a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='streamnest-download'; a.click(); URL.revokeObjectURL(a.href); $('status').textContent='Your download is ready.';
  } catch(err){$('status').textContent=err.message} finally {$('download').disabled=false}});
</script></body></html>"""


def _engine(output_dir: Path) -> MediaDownloader:
    config = Config(download_directory=str(output_dir), default_video_format="mp4")
    return MediaDownloader(config, Console(stderr=True))


def _error_response(exc: Exception):
    if isinstance(exc, DownloadError):
        message = exc.message
    else:
        message = str(exc) or "The request could not be completed."
    return jsonify({"error": message}), 400


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/api/analyze")
def analyze():
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    try:
        url = str(payload.get("url", ""))
        info = _engine(Path(tempfile.gettempdir()) / "streamnest").analyze(url)
        duration = info.get("duration")
        duration_text = f"{int(duration) // 60}:{int(duration) % 60:02d}" if duration else ""
        return jsonify({
            "title": info.get("title", "Untitled media"),
            "platform": info.get("_platform", ""),
            "duration": duration_text,
            "uploader": info.get("uploader", ""),
            "thumbnail": info.get("thumbnail", ""),
            "playlist": is_playlist(info),
        })
    except (SecurityError, DownloadError, ValueError) as exc:
        return _error_response(exc)


@app.post("/api/download")
def download():
    payload: dict[str, Any] = request.get_json(silent=True) or {}
    url = str(payload.get("url", ""))
    kind = str(payload.get("kind", "video"))
    quality = str(payload.get("quality", "best"))
    output_format = str(payload.get("format", "mp4"))
    if kind not in {"video", "audio"} or quality not in _VIDEO_SELECTORS:
        return jsonify({"error": "Invalid download options."}), 400
    if kind == "audio" and output_format not in _AUDIO_FORMATS:
        return jsonify({"error": "Invalid audio format."}), 400
    if kind == "video" and output_format not in {"mp4", "webm"}:
        return jsonify({"error": "Invalid video format."}), 400
    output_dir = Path(tempfile.mkdtemp(prefix="streamnest-"))
    try:
        engine = _engine(output_dir)
        if kind == "audio":
            result = engine.download_audio(url, codec=output_format, quality=None, show_stages=False)
        else:
            result = engine.download_media(url, selector=_VIDEO_SELECTORS[quality],
                                           container=output_format, show_stages=False)
        path = Path(result.filepath)
        if not path.is_file():
            return jsonify({"error": "The download completed without producing a file."}), 500
        return send_file(path, as_attachment=True,
                         download_name=sanitize_filename(path.name))
    except (SecurityError, DownloadError, ValueError) as exc:
        return _error_response(exc)
