"""
Small shared utilities.
"""
from urllib.parse import urlparse

# Domains that should be routed through yt-dlp instead of a plain HTTP download.
YTDLP_DOMAINS = [
    "youtube.com", "youtu.be", "music.youtube.com",
    "vimeo.com", "tiktok.com", "twitter.com", "x.com",
    "facebook.com", "fb.watch", "instagram.com",
    "soundcloud.com", "dailymotion.com", "twitch.tv",
    "reddit.com", "bilibili.com", "streamable.com",
]


def is_ytdlp_url(url: str) -> bool:
    """Return True if the URL belongs to a site that needs yt-dlp
    (video/audio extraction) rather than a direct file download."""
    try:
        netloc = urlparse(url).netloc.lower()
    except ValueError:
        return False
    return any(domain in netloc for domain in YTDLP_DOMAINS)
