"""
Posts to an Instagram Business/Creator account using the Meta Graph API.
Handles both images and video (Reels) — media type is auto-detected from
media_url's file extension (see media_utils.py), or pass media_type
explicitly to skip detection.

Required environment variables:
  IG_USER_ID     - the numeric Instagram Business account ID (not your @handle)
  IG_ACCESS_TOKEN - a long-lived access token with instagram_content_publish scope
                     (reading insights also needs instagram_manage_insights)

Note: Instagram requires media_url to be a PUBLICLY reachable URL.
It cannot accept a local file — the image or video must already be
hosted somewhere (e.g. a GitHub raw URL, a cloud storage bucket, or a CDN).

Instagram posting is always a two-step process:
  1. Create a media container (upload the image/video + caption)
  2. Publish that container

Videos need an extra wait: Instagram processes the video after the
container is created, and publishing before it's ready will fail. This
module polls the container's status_code until it's FINISHED (or fails)
before attempting to publish.

Carousel posts (post_carousel) are a three-step variant of the same idea:
  1. Create one child container per item, each flagged is_carousel_item
  2. Create a parent CAROUSEL container referencing all the child ids
  3. Publish the parent container — same _publish() used for single posts
Instagram requires 2-10 items per carousel; children can be images or
video, mixed freely, same auto-detection as a single post.
"""

import os
import time
import requests

from .media_utils import detect_media_type

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# How long to wait for Instagram to finish processing an uploaded video
# before giving up. Reels processing is usually well under this on
# typical launch-campaign clip lengths. Also applies to any video used
# as a carousel child.
VIDEO_PROCESSING_TIMEOUT_SECONDS = 300
VIDEO_POLL_INTERVAL_SECONDS = 5

# Reels report "views"; feed images/videos report "reach" instead.
# Note: 'impressions' is deprecated across all media types as of recent
# Graph API versions and always errors — deliberately excluded here.
# Note: 'plays' was Reels' original metric name but Meta now rejects it —
# confirmed 2026-09-16 (day33-instagram metrics fetch) — 'views' is the
# current valid name for the same thing.
IMAGE_METRICS = "reach,likes,comments,saved,shares"
REELS_METRICS = "views,reach,likes,comments,saved,shares"

# Instagram's own limits on how many items a single carousel can contain.
CAROUSEL_MIN_ITEMS = 2
CAROUSEL_MAX_ITEMS = 10


def _create_container(ig_user_id: str, access_token: str, caption: str, payload_extra: dict) -> str:
    create_url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    create_payload = {
        "caption": caption,
        "access_token": access_token,
        **payload_extra,
    }
    create_resp = requests.post(create_url, data=create_payload, timeout=30)
    if create_resp.status_code >= 400:
        raise RuntimeError(f"Instagram container creation failed ({create_resp.status_code}): {create_resp.text}")
    return create_resp.json()["id"]


def _wait_for_video_ready(creation_id: str, access_token: str) -> None:
    status_url = f"{GRAPH_API_BASE}/{creation_id}"
    elapsed = 0
    while elapsed < VIDEO_PROCESSING_TIMEOUT_SECONDS:
        status_resp = requests.get(
            status_url,
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        if status_resp.status_code >= 400:
            raise RuntimeError(f"Instagram status check failed ({status_resp.status_code}): {status_resp.text}")

        status_code = status_resp.json().get("status_code")
        if status_code == "FINISHED":
            return
        if status_code == "ERROR":
            raise RuntimeError(f"Instagram failed to process the video (container {creation_id})")

        time.sleep(VIDEO_POLL_INTERVAL_SECONDS)
        elapsed += VIDEO_POLL_INTERVAL_SECONDS

    raise RuntimeError(
        f"Instagram video processing did not finish within {VIDEO_PROCESSING_TIMEOUT_SECONDS}s "
        f"(container {creation_id})"
    )


def _publish(ig_user_id: str, access_token: str, creation_id: str) -> dict:
    publish_url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    publish_resp = requests.post(publish_url, data=publish_payload, timeout=30)
    if publish_resp.status_code >= 400:
        raise RuntimeError(f"Instagram publish failed ({publish_resp.status_code}): {publish_resp.text}")
    return publish_resp.json()


def post(caption: str, media_url: str = "", media_type: str = "") -> dict:
    if not media_url:
        raise ValueError("Instagram posts require a media_url (image or video)")

    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    resolved_type = media_type or detect_media_type(media_url)

    if resolved_type == "video":
        creation_id = _create_container(
            ig_user_id, access_token, caption,
            {"media_type": "REELS", "video_url": media_url},
        )
        _wait_for_video_ready(creation_id, access_token)
    elif resolved_type == "image":
        creation_id = _create_container(
            ig_user_id, access_token, caption,
            {"image_url": media_url},
        )
        # Images process fast enough that Instagram doesn't require polling
        # here, but a short pause avoids the rare "container not ready yet"
        # publish error.
        time.sleep(5)
    else:
        raise ValueError(
            f"Could not determine media type for '{media_url}'. "
            "Pass media_type='image' or media_type='video' explicitly, "
            "or use a URL with a recognized file extension."
        )

    return _publish(ig_user_id, access_token, creation_id)


def _create_carousel_child(ig_user_id: str, access_token: str, media_url: str) -> str:
    """Creates one child container for a carousel item. Children don't
    carry their own caption — only the parent carousel container does,
    same as how Instagram's own app treats multi-image posts."""
    resolved_type = detect_media_type(media_url)

    if resolved_type == "video":
        creation_id = _create_container(
            ig_user_id, access_token, "",
            {"media_type": "VIDEO", "video_url": media_url, "is_carousel_item": "true"},
        )
        _wait_for_video_ready(creation_id, access_token)
    elif resolved_type == "image":
        creation_id = _create_container(
            ig_user_id, access_token, "",
            {"image_url": media_url, "is_carousel_item": "true"},
        )
    else:
        raise ValueError(
            f"Could not determine media type for carousel item '{media_url}'. "
            "Use a URL with a recognized file extension."
        )

    return creation_id


def post_carousel(caption: str, media_urls: list) -> dict:
    """Posts a carousel — multiple images/video in one swipeable post.
    Each item becomes its own child container first, then a parent
    CAROUSEL container ties them together and gets published, same as a
    single post's create-then-publish flow.

    NOTE: this has not yet been run against a live account. Do a
    supervised test post before trusting it in the scheduled run —
    same caution as any newly-wired endpoint in this codebase.
    """
    if not media_urls:
        raise ValueError("Instagram carousel posts require at least one media_url in media_urls")
    if len(media_urls) < CAROUSEL_MIN_ITEMS:
        raise ValueError(
            f"Instagram carousels need at least {CAROUSEL_MIN_ITEMS} items — "
            "use post() for a single image or video"
        )
    if len(media_urls) > CAROUSEL_MAX_ITEMS:
        raise ValueError(f"Instagram carousels support at most {CAROUSEL_MAX_ITEMS} items, got {len(media_urls)}")

    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    child_ids = [_create_carousel_child(ig_user_id, access_token, url) for url in media_urls]

    creation_id = _create_container(
        ig_user_id, access_token, caption,
        {"media_type": "CAROUSEL", "children": ",".join(child_ids)},
    )
    # Same short settle pause used for a plain image post above, before
    # the parent carousel container is published.
    time.sleep(5)

    return _publish(ig_user_id, access_token, creation_id)


def get_insights(media_id: str, media_type: str = "") -> dict:
    """Fetches engagement metrics for a published IG post or Reel.

    media_type ('image' or 'video') picks the right metric set — Reels
    report 'plays' where feed images report 'impressions'. If omitted,
    tries Reels metrics first and falls back to image metrics, since the
    API rejects unsupported metrics for a given object rather than just
    omitting them.
    """
    ig_user_id = os.environ["IG_USER_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]
    url = f"{GRAPH_API_BASE}/{media_id}/insights"

    metric_sets = []
    if media_type == "video":
        metric_sets = [REELS_METRICS]
    elif media_type == "image":
        metric_sets = [IMAGE_METRICS]
    else:
        metric_sets = [REELS_METRICS, IMAGE_METRICS]

    last_error = None
    for metrics in metric_sets:
        response = requests.get(
            url,
            params={"metric": metrics, "access_token": access_token},
            timeout=30,
        )
        if response.status_code < 400:
            values = {
                item["name"]: item.get("values", [{}])[0].get("value", 0)
                for item in response.json().get("data", [])
            }
            return values
        last_error = response.text

    raise RuntimeError(f"Instagram insights fetch failed for {media_id}: {last_error}")
