"""
Posts a Pin (image or video) to Pinterest using the Pinterest API v5.
Live and confirmed working as of September 2026.

Required environment variables:
  PINTEREST_CLIENT_ID
  PINTEREST_CLIENT_SECRET
  PINTEREST_REFRESH_TOKEN   - long-lived (60 days from issue, refreshable
                                indefinitely), used to fetch a fresh access
                                token on every run rather than storing a
                                short-lived (30-day) access token directly.
                                This mirrors tiktok.py's approach — the
                                same fix for the Instagram token-expiry
                                issue this campaign already hit once.
  PINTEREST_BOARD_ID

Notes:
  - Image pins are a single call: create the pin with an image_url source.
  - Video pins are a two-step process: register a media upload, upload the
    video file to the URL Pinterest gives you, wait for Pinterest to finish
    processing it, THEN create the pin referencing that media_id. This
    mirrors Instagram's container-then-publish pattern but with an extra
    "register the upload" step first.
"""

import base64
import os
import time
import requests

from .media_utils import detect_media_type

API_BASE = "https://api.pinterest.com/v5"
TOKEN_URL = f"{API_BASE}/oauth/token"

VIDEO_PROCESSING_TIMEOUT_SECONDS = 300
VIDEO_POLL_INTERVAL_SECONDS = 5


def _get_fresh_access_token() -> str:
    client_id = os.environ["PINTEREST_CLIENT_ID"]
    client_secret = os.environ["PINTEREST_CLIENT_SECRET"]
    refresh_token = os.environ["PINTEREST_REFRESH_TOKEN"]

    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(TOKEN_URL, headers=headers, data=payload, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Pinterest token refresh failed ({response.status_code}): {response.text}")
    return response.json()["access_token"]


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _create_pin(access_token: str, board_id: str, caption: str, media_source: dict) -> dict:
    url = f"{API_BASE}/pins"
    payload = {
        "board_id": board_id,
        "description": caption,
        "media_source": media_source,
    }
    response = requests.post(url, json=payload, headers=_headers(access_token), timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Pinterest pin creation failed ({response.status_code}): {response.text}")
    return response.json()


def _upload_video_and_get_media_id(access_token: str, media_url: str) -> str:
    register_url = f"{API_BASE}/media"
    register_resp = requests.post(
        register_url,
        json={"media_type": "video"},
        headers=_headers(access_token),
        timeout=30,
    )
    if register_resp.status_code >= 400:
        raise RuntimeError(f"Pinterest media registration failed ({register_resp.status_code}): {register_resp.text}")
    register_data = register_resp.json()
    media_id = register_data["media_id"]
    upload_url = register_data["upload_url"]
    upload_params = register_data.get("upload_parameters", {})

    video_resp = requests.get(media_url, timeout=60)
    if video_resp.status_code >= 400:
        raise RuntimeError(f"Could not download video from media_url ({video_resp.status_code})")

    files = {"file": ("video.mp4", video_resp.content)}
    upload_resp = requests.post(upload_url, data=upload_params, files=files, timeout=120)
    if upload_resp.status_code >= 400:
        raise RuntimeError(f"Pinterest video upload failed ({upload_resp.status_code}): {upload_resp.text}")

    status_url = f"{API_BASE}/media/{media_id}"
    elapsed = 0
    while elapsed < VIDEO_PROCESSING_TIMEOUT_SECONDS:
        status_resp = requests.get(status_url, headers=_headers(access_token), timeout=30)
        if status_resp.status_code >= 400:
            raise RuntimeError(f"Pinterest media status check failed ({status_resp.status_code}): {status_resp.text}")
        status = status_resp.json().get("status")
        if status == "succeeded":
            return media_id
        if status == "failed":
            raise RuntimeError(f"Pinterest failed to process the video (media_id {media_id})")
        time.sleep(VIDEO_POLL_INTERVAL_SECONDS)
        elapsed += VIDEO_POLL_INTERVAL_SECONDS

    raise RuntimeError(
        f"Pinterest video processing did not finish within {VIDEO_PROCESSING_TIMEOUT_SECONDS}s "
        f"(media_id {media_id})"
    )


def post(caption: str, media_url: str = "", media_type: str = "") -> dict:
    if not media_url:
        raise ValueError("Pinterest pins require a media_url (image or video) — Pinterest has no text-only pin")

    access_token = _get_fresh_access_token()
    board_id = os.environ["PINTEREST_BOARD_ID"]

    resolved_type = media_type or detect_media_type(media_url)

    if resolved_type == "image":
        return _create_pin(access_token, board_id, caption, {"source_type": "image_url", "url": media_url})
    elif resolved_type == "video":
        media_id = _upload_video_and_get_media_id(access_token, media_url)
        return _create_pin(access_token, board_id, caption, {"source_type": "video_id", "media_id": media_id})
    else:
        raise ValueError(
            f"Could not determine media type for '{media_url}'. "
            "Pass media_type='image' or media_type='video' explicitly, "
            "or use a URL with a recognized file extension."
        )


def get_insights(pin_id: str) -> dict:
    """Fetches engagement metrics for a published Pin using Pinterest's
    analytics endpoint.

    Pinterest's per-pin analytics need a date range rather than returning
    a simple running total, so this requests the last 90 days up to today
    and sums across that window — wide enough to cover this campaign's
    full posting history without needing per-post logic for how long ago
    each pin went up.
    """
    from datetime import datetime, timedelta, timezone

    access_token = _get_fresh_access_token()
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=90)

    url = f"{API_BASE}/pins/{pin_id}/analytics"
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "metric_types": "IMPRESSION,PIN_CLICK,OUTBOUND_CLICK,SAVE",
    }
    response = requests.get(url, params=params, headers=_headers(access_token), timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Pinterest insights fetch failed ({response.status_code}): {response.text}")

    data = response.json().get("all", {}).get("summary_metrics", {})
    return {
        "impressions": data.get("IMPRESSION", 0),
        "pin_clicks": data.get("PIN_CLICK", 0),
        "outbound_clicks": data.get("OUTBOUND_CLICK", 0),
        "saves": data.get("SAVE", 0),
    }
