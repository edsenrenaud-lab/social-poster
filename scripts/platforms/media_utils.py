"""
Shared helper for figuring out whether a media_url points to an image or
a video, so each platform module can route to the right upload path.

Add extensions here as new formats come up — this is the single place
every platform script checks.
"""

from urllib.parse import urlparse

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}


def detect_media_type(media_url: str) -> str:
    """Returns 'image', 'video', or 'unknown' based on the URL's file extension."""
    if not media_url:
        return "unknown"

    path = urlparse(media_url).path.lower()
    for ext in IMAGE_EXTENSIONS:
        if path.endswith(ext):
            return "image"
    for ext in VIDEO_EXTENSIONS:
        if path.endswith(ext):
            return "video"
    return "unknown"
