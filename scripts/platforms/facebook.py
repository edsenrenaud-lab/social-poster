"""
Posts to a Facebook Page using the Meta Graph API. Handles images, videos,
and text-only posts — the media type is auto-detected from media_url's
file extension (see media_utils.py), or pass media_type explicitly to skip
detection.

Required environment variables:
  FB_PAGE_ID            - the numeric ID of your Facebook Page
  FB_PAGE_ACCESS_TOKEN  - a long-lived Page access token with pages_manage_posts scope

Notes:
  - Images and text posts publish immediately.
  - Videos are uploaded via the /{page-id}/videos edge using a hosted
    file_url (same GitHub-raw-URL pattern used for images). Facebook
    processes the video asynchronously on their end after upload, but
    the API call itself returns as soon as the upload is accepted —
    no polling is required to publish (the post appears once
    processing finishes on Facebook's side, generally shortly after).
"""

import os
import requests

from media_utils import detect_media_type

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _post_image(page_id: str, access_token: str, caption: str, media_url: str) -> dict:
    url = f"{GRAPH_API_BASE}/{page_id}/photos"
    payload = {
        "url": media_url,
        "caption": caption,
        "access_token": access_token,
    }
    response = requests.post(url, data=payload, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Facebook photo post failed ({response.status_code}): {response.text}")
    return response.json()


def _post_video(page_id: str, access_token: str, caption: str, media_url: str) -> dict:
    url = f"{GRAPH_API_BASE}/{page_id}/videos"
    payload = {
        "file_url": media_url,
        "description": caption,
        "access_token": access_token,
    }
    # Video uploads can take longer than the default timeout to be accepted,
    # especially for larger files — give this one more room.
    response = requests.post(url, data=payload, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(f"Facebook video post failed ({response.status_code}): {response.text}")
    return response.json()


def _post_text(page_id: str, access_token: str, caption: str) -> dict:
    url = f"{GRAPH_API_BASE}/{page_id}/feed"
    payload = {
        "message": caption,
        "access_token": access_token,
    }
    response = requests.post(url, data=payload, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Facebook text post failed ({response.status_code}): {response.text}")
    return response.json()


def post(caption: str, media_url: str = "", media_type: str = "") -> dict:
    page_id = os.environ["FB_PAGE_ID"]
    access_token = os.environ["FB_PAGE_ACCESS_TOKEN"]

    if not media_url:
        return _post_text(page_id, access_token, caption)

    resolved_type = media_type or detect_media_type(media_url)

    if resolved_type == "video":
        return _post_video(page_id, access_token, caption, media_url)
    elif resolved_type == "image":
        return _post_image(page_id, access_token, caption, media_url)
    else:
        raise ValueError(
            f"Could not determine media type for '{media_url}'. "
            "Pass media_type='image' or media_type='video' explicitly, "
            "or use a URL with a recognized file extension."
        )
