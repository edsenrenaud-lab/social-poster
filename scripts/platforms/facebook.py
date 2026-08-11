"""
Posts to a Facebook Page using the Meta Graph API.

Required environment variables:
  FB_PAGE_ID            - the numeric ID of your Facebook Page
  FB_PAGE_ACCESS_TOKEN  - a long-lived Page access token with pages_manage_posts scope
"""

import os
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def post(caption: str, media_url: str = "") -> dict:
    page_id = os.environ["FB_PAGE_ID"]
    access_token = os.environ["FB_PAGE_ACCESS_TOKEN"]

    if media_url:
        url = f"{GRAPH_API_BASE}/{page_id}/photos"
        payload = {
            "url": media_url,
            "caption": caption,
            "access_token": access_token,
        }
    else:
        url = f"{GRAPH_API_BASE}/{page_id}/feed"
        payload = {
            "message": caption,
            "access_token": access_token,
        }

    response = requests.post(url, data=payload, timeout=30)

    if response.status_code >= 400:
        raise RuntimeError(f"Facebook post failed ({response.status_code}): {response.text}")

    return response.json()
