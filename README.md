# 💜 Purple Download Manager

An all-in-one file downloader with a fully animated PyQt5 interface — now with
**yt-dlp** built in for video/audio sites, alongside plain direct-link downloads.

- Slowly swirling **purple → pink gradient background**
- **Glowing buttons** that pulse with a soft shadow on hover
- **Smoothly animated progress bars** whose fill color pulses purple ↔ pink while active, and turns green/red on success/error
- Animated **color-cycling title text**
- Multi-file **download queue** — add URLs one at a time, paste multiple lines, or drag & drop a `.txt` file of links
- **Automatic engine detection**: regular file links use a fast direct HTTP downloader; links from YouTube, TikTok, X/Twitter, Instagram, Facebook, SoundCloud, Vimeo, Twitch, Reddit, etc. are automatically routed through **yt-dlp**
- Optional **🎵 Audio only (MP3)** mode for yt-dlp links
- Per-file **Start / Pause / Cancel** controls (pause is disabled for yt-dlp rows, since yt-dlp streams can't be paused/resumed), plus **Start All / Pause All / Clear Completed**
- Live **speed** and **ETA** readout per download
- Built-in **activity log console**

## Folder structure

```
PurpleDownloader/
├── main.py                # entry point
├── requirements.txt
├── gui/
│   ├── theme.py            # purple palette, animated gradient background, QSS
│   ├── widgets.py           # GlowButton, AnimatedProgressBar
│   └── main_window.py       # main window / app logic, engine routing
└── core/
    ├── downloader.py        # QThread worker for plain direct HTTP downloads
    ├── ytdlp_worker.py       # QThread worker wrapping yt-dlp (video/audio sites)
    └── utils.py              # URL → engine detection (is_ytdlp_url)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Requires **Python 3.8+**.

### ffmpeg (required for yt-dlp video merging / MP3 extraction)

yt-dlp needs **ffmpeg** on your system PATH to merge separate video+audio streams
into one file, and to extract audio as MP3.

- **Windows**: download from https://ffmpeg.org/download.html and add the `bin` folder to PATH, or `choco install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` (Debian/Ubuntu) or your distro's equivalent

Without ffmpeg, yt-dlp will still work but may only be able to grab pre-merged
lower-quality formats, and MP3 extraction won't be available.

## Usage

1. Paste a URL into the input box and press **Enter** or click **＋ Add**.
   - Regular file links (`.zip`, `.pdf`, images, installers, etc.) download directly.
   - YouTube/TikTok/X/Instagram/SoundCloud/etc. links are automatically handled by yt-dlp — the **Mode** column shows `🎬 yt-dlp` or `📄 Direct`.
2. Tick **🎵 Audio only (MP3)** *before* adding a yt-dlp link if you just want the audio track.
3. Click **▶** on a row to start that download, or **▶ Start All** to start everything queued.
4. Use **⏸** to pause/resume a direct download, or **✕** to cancel any download (direct or yt-dlp).
5. Click **Change folder** to choose where files are saved (defaults to your `Downloads` folder).
6. Drag and drop a `.txt` file containing one URL per line to bulk-import links, or use **Import .txt**.
7. Click **🧹 Clear Completed** to tidy up the list once files are done.

## Notes

- Downloads run on background `QThread`s so the animated UI never freezes.
- Direct-download filenames are inferred from the `Content-Disposition` header when available, otherwise from the URL path. yt-dlp filenames use the media title.
- yt-dlp downloads can be **cancelled** but not paused/resumed mid-stream — this is a yt-dlp/site limitation, not this app's.
- Some sites may require you to be logged in (cookies) for certain content — that's outside the scope of this simple UI, but yt-dlp itself supports `--cookies` if you want to extend `ytdlp_worker.py`.

## Customizing the theme

All colors live at the top of `gui/theme.py` — change `PURPLE_ACCENT`, `PINK_ACCENT`, etc. to retheme the entire app in one place.

## Customizing which sites use yt-dlp

Edit `YTDLP_DOMAINS` in `core/utils.py` to add or remove domains that should be routed through yt-dlp instead of the direct downloader.

