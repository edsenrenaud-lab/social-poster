"""
Posts a video to TikTok as a draft (lands in your TikTok inbox for you to
review and manually publish) using the Content Posting API.

This is intentionally NOT full silent auto-publish — that requires TikTok's
app audit process. This draft-mode flow works today without an audit.

Required environment variables:
  TIKTOK_CLIENT_KEY
  TIKTOK_CLIENT_SECRET
  TIKTOK_REFRESH_TOKEN   - long-lived (1 year), used to fetch a fresh
                            access token on every run
"""

import os
import requests

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
UPLOAD_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"


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


def post(caption: str, media_url: str = "") -> dict:
    if not media_url:
        raise ValueError("TikTok posts require a media_url pointing to a public video file")

    access_token = _get_fresh_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": media_url,
        }
    }

    response = requests.post(UPLOAD_INIT_URL, json=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"TikTok draft upload failed ({response.status_code}): {response.text}")

    return response.json()
