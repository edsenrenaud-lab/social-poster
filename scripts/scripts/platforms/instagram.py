"""
Posts to an Instagram Business/Creator account using the Meta Graph API.

Instagram posting is a two-step process:
  1. Create a media container (upload the image + caption)
  2. Publish that container

Required environment variables:
  IG_USER_ID     - the numeric Instagram Business account ID (not your @handle)
  IG_ACCESS_TOKEN - a long-lived access token with instagram_content_publish scope

Note: Instagram requires media_url to be a PUBLICLY reachable image URL.
It cannot accept a local file — the image must already be hosted somewhere
(e.g. a GitHub raw URL, a cloud storage bucket, or a CDN).
"""

import os
import time
import requests

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def post(caption: str, media_url: str = "") -> dict:
    if not media_url:
        raise ValueError("Instagram posts require a media_url (image posts only, for now)")

    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    create_url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    create_payload = {
        "image_url": media_url,
        "caption": caption,
        "access_token": access_token,
    }
    create_resp = requests.post(create_url, data=create_payload, timeout=30)
    if create_resp.status_code >= 400:
        raise RuntimeError(f"Instagram container creation failed ({create_resp.status_code}): {create_resp.text}")

    creation_id = create_resp.json()["id"]

    time.sleep(5)

    publish_url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    publish_resp = requests.post(publish_url, data=publish_payload, timeout=30)
    if publish_resp.status_code >= 400:
        raise RuntimeError(f"Instagram publish failed ({publish_resp.status_code}): {publish_resp.text}")

    return publish_resp.json()
