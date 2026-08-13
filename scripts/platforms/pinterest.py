"""
Posts a Pin (image or video) to Pinterest using the Pinterest API v5.
Wired up and ready to go — just needs your trial access approved and
the environment variables below filled in.

Required environment variables:
  PINTEREST_ACCESS_TOKEN
  PINTEREST_BOARD_ID

Notes:
  - Image pins are a single call: create the pin with an image_url source.
  - Video pins are a two-step process: register a media upload, upload the
    video file to the URL Pinterest gives you, wait for Pinterest to finish
    processing it, THEN create the pin referencing that media_id. This
    mirrors Instagram's container-then-publish pattern but with an extra
    "register the upload" step first.
  - IMPORTANT: this module hasn't been run against a live, approved
    Pinterest account yet (trial access was still pending as of this
    write-up). Once access comes through, do a supervised test post
    before trusting it in the scheduled run — Pinterest's API details
    can shift, so re-check https://developers.pinterest.com/docs/api/v5/
    if anything here doesn't match what you see.
"""

import os
import time
import requests

from .media_utils import detect_media_type

API_BASE = "https://api.pinterest.com/v5"

VIDEO_PROCESSING_TIMEOUT_SECONDS = 300
VIDEO_POLL_INTERVAL_SECONDS = 5


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
    # Step 1: register the upload, get a media_id plus an upload URL/fields
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

    # Step 2: download our own video, then upload it as multipart form
    # data to the URL Pinterest just gave us.
    video_resp = requests.get(media_url, timeout=60)
    if video_resp.status_code >= 400:
        raise RuntimeError(f"Could not download video from media_url ({video_resp.status_code})")

    files = {"file": ("video.mp4", video_resp.content)}
    upload_resp = requests.post(upload_url, data=upload_params, files=files, timeout=120)
    if upload_resp.status_code >= 400:
        raise RuntimeError(f"Pinterest video upload failed ({upload_resp.status_code}): {upload_resp.text}")

    # Step 3: poll until Pinterest finishes processing the video
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

    access_token = os.environ["PINTEREST_ACCESS_TOKEN"]
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
