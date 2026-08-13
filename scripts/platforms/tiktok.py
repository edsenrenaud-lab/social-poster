"""
Posts to TikTok as a draft (lands in your TikTok inbox for you to review
and manually publish) using the Content Posting API. Handles both video
and photo posts — media type is auto-detected from media_url's file
extension (see media_utils.py), or pass media_type explicitly to skip
detection.

Uses direct file upload rather than PULL_FROM_URL, since PULL_FROM_URL
requires TikTok domain-ownership verification of the media host.

This is intentionally NOT full silent auto-publish — that requires TikTok's
app audit process. This draft-mode flow works today without an audit.

Required environment variables:
  TIKTOK_CLIENT_KEY
  TIKTOK_CLIENT_SECRET
  TIKTOK_REFRESH_TOKEN   - long-lived (1 year), used to fetch a fresh
                            access token on every run

Status:
  - Video path: tested and confirmed working live.
  - Photo path: wired up against TikTok's photo Content Posting API but
    NOT yet run against a live account. Do a supervised test post before
    trusting it in the scheduled run, and re-check
    https://developers.tiktok.com/doc/content-posting-api-reference-upload-photo/
    if anything here doesn't match — TikTok's photo API is newer and less
    stable than their video API.
"""

import os
import requests

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
VIDEO_UPLOAD_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
PHOTO_UPLOAD_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"

from .media_utils import detect_media_type


def _get_fresh_access_token() -> str:
    payload = {
        "client_key": os.environ["TIKTOK_CLIENT_KEY"],
        "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["TIKTOK_REFRESH_TOKEN"],
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"TikTok token refresh failed ({response.status_code}): {response.text}")
    return response.json()["access_token"]


def _post_video(access_token: str, media_url: str) -> dict:
    # Download the video ourselves rather than asking TikTok to fetch it
    video_response = requests.get(media_url, timeout=60)
    if video_response.status_code >= 400:
        raise RuntimeError(f"Could not download video from media_url ({video_response.status_code})")
    video_bytes = video_response.content
    video_size = len(video_bytes)

    init_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    init_payload = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1,
        }
    }
    init_resp = requests.post(VIDEO_UPLOAD_INIT_URL, json=init_payload, headers=init_headers, timeout=30)
    if init_resp.status_code >= 400:
        raise RuntimeError(f"TikTok video upload init failed ({init_resp.status_code}): {init_resp.text}")

    init_data = init_resp.json()["data"]
    upload_url = init_data["upload_url"]
    publish_id = init_data["publish_id"]

    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
    }
    upload_resp = requests.put(upload_url, data=video_bytes, headers=upload_headers, timeout=120)
    if upload_resp.status_code >= 400:
        raise RuntimeError(f"TikTok video upload failed ({upload_resp.status_code}): {upload_resp.text}")

    return {"id": publish_id}


def _post_photo(access_token: str, caption: str, media_url: str) -> dict:
    # Photo drafts go through the general "content" init endpoint rather
    # than the video-specific inbox endpoint, and reference the photo by
    # a publicly reachable URL (PULL_FROM_URL) rather than a raw byte
    # upload — TikTok's photo API expects the image(s) to already be
    # hosted, same as the Facebook/Instagram image flow.
    init_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    init_payload = {
        "post_info": {
            "title": caption,
            "privacy_level": "SELF_ONLY",
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_cover_index": 0,
            "photo_images": [media_url],
        },
        "post_mode": "MEDIA_UPLOAD",
        "media_type": "PHOTO",
    }
    init_resp = requests.post(PHOTO_UPLOAD_INIT_URL, json=init_payload, headers=init_headers, timeout=30)
    if init_resp.status_code >= 400:
        raise RuntimeError(f"TikTok photo upload init failed ({init_resp.status_code}): {init_resp.text}")

    init_data = init_resp.json()["data"]
    return {"id": init_data.get("publish_id", "")}


def post(caption: str, media_url: str = "", media_type: str = "") -> dict:
    if not media_url:
        raise ValueError("TikTok posts require a media_url pointing to a video or photo file")

    access_token = _get_fresh_access_token()
    resolved_type = media_type or detect_media_type(media_url)

    if resolved_type == "video":
        return _post_video(access_token, media_url)
    elif resolved_type == "image":
        return _post_photo(access_token, caption, media_url)
    else:
        raise ValueError(
            f"Could not determine media type for '{media_url}'. "
            "Pass media_type='image' or media_type='video' explicitly, "
            "or use a URL with a recognized file extension."
        )
