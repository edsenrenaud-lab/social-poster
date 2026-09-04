"""
Reads schedule.json, finds posts that are due, publishes them to the
right platform, and updates their status in place.

Run this on a schedule (see .github/workflows/scheduler.yml) — each run
checks for anything due since the last run and posts it.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from platforms import facebook, instagram, pinterest, tiktok

SCHEDULE_PATH = Path(__file__).parent.parent / "schedule.json"

PLATFORM_HANDLERS = {
    "facebook": facebook.post,
    "instagram": instagram.post,
    "pinterest": pinterest.post,
    "tiktok": tiktok.post,
}

# How many times to attempt a post before giving up, and how long to wait
# between attempts (seconds). Kept short since this all happens within one
# GitHub Actions job run.
MAX_ATTEMPTS = 3
RETRY_DELAYS = [30, 120]  # wait 30s before attempt 2, 120s before attempt 3 —
                          # widened from [15, 45] after a Facebook video-publish
                          # error cleared on manual retry minutes later but
                          # wasn't recoverable within the original short window

# The scheduler workflow runs every 15 minutes, so a "failed" entry can also
# be retried across separate runs, not just within a single run's short
# in-process retries above. Capped so a genuinely broken entry (bad
# credentials, invalid media, wrong platform) doesn't retry forever and spam
# the failure-notification alert every 15 minutes — it still fails and
# alerts, just a bounded number of times rather than indefinitely.
MAX_SCHEDULED_RETRIES = 4  # roughly 1 hour of retries at the 15-min interval

# Signatures of errors known to be transient (network hiccups, rate limits,
# platform-side outages) rather than real problems (bad credentials, invalid
# media, unknown platform). Only these get retried automatically — anything
# else fails immediately, same as before, so a real problem still surfaces
# right away instead of silently retrying something that will never succeed.
TRANSIENT_PATTERNS = [
    r"\(429\)",                     # rate limited
    r"\(50[0-4]\)",                 # 500/501/502/503/504 server errors
    r"first byte timeout",          # CDN/network timeout (seen from TikTok)
    r"Generic Internal Error",      # Meta's intermittent IG publish error
    r"error_subcode\":2207085",     # the specific Meta error code seen so far
    r"Could not download",         # transient fetch failure from media_url
    r"failed to process the video", # platform-side processing timeout
    r"Connection (aborted|reset|refused)",
    r"Read timed out",
    r"No permission to publish the video",  # intermittent Facebook video-fetch
                                             # glitch — sounds permanent but has
                                             # been observed to clear on retry;
                                             # confirmed 2026-09-04
]


def is_transient(error_message: str) -> bool:
    return any(re.search(pattern, error_message, re.IGNORECASE) for pattern in TRANSIENT_PATTERNS)


def load_schedule() -> list:
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)


def save_schedule(entries: list) -> None:
    with open(SCHEDULE_PATH, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")


def is_due(entry: dict, now: datetime) -> bool:
    scheduled_time = datetime.fromisoformat(entry["datetime"].replace("Z", "+00:00"))
    if scheduled_time > now:
        return False

    status = entry.get("status")
    if status == "pending":
        return True

    # A previously-failed entry gets picked back up on a later run only if
    # its error looked transient (not a permanent problem like bad
    # credentials or invalid media) and it hasn't already used up its
    # cross-run retry budget.
    if status == "failed" and entry.get("scheduled_retry_count", 0) < MAX_SCHEDULED_RETRIES:
        return is_transient(entry.get("error", ""))

    return False


def post_with_retry(handler, entry: dict) -> dict:
    """Attempts the post, retrying only on errors that look transient.
    Raises the final exception if every attempt fails."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return handler(
                entry.get("caption", ""),
                entry.get("media_url", ""),
                entry.get("media_type", ""),
            )
        except Exception as e:
            last_error = e
            error_str = str(e)
            if attempt < MAX_ATTEMPTS and is_transient(error_str):
                delay = RETRY_DELAYS[attempt - 1]
                print(f"[{entry['id']}] Attempt {attempt} failed with a transient-looking "
                      f"error — retrying in {delay}s: {error_str}")
                time.sleep(delay)
                continue
            raise last_error
    raise last_error


def main() -> None:
    now = datetime.now(timezone.utc)
    entries = load_schedule()
    changed = False
    had_failure = False

    for entry in entries:
        if not is_due(entry, now):
            continue

        platform = entry.get("platform")
        handler = PLATFORM_HANDLERS.get(platform)

        if handler is None:
            print(f"[{entry['id']}] Unknown platform '{platform}' — skipping")
            entry["status"] = "failed"
            entry["error"] = f"Unknown platform: {platform}"
            changed = True
            had_failure = True
            continue

        try:
            print(f"[{entry['id']}] Posting to {platform}...")
            result = post_with_retry(handler, entry)
            entry["status"] = "posted"
            entry["posted_at"] = now.isoformat()
            entry["result_id"] = result.get("id", "")
            print(f"[{entry['id']}] Success — {platform} post ID {entry['result_id']}")
        except Exception as e:
            was_scheduled_retry = entry.get("status") == "failed"
            retry_count = entry.get("scheduled_retry_count", 0)
            if was_scheduled_retry:
                retry_count += 1

            print(f"[{entry['id']}] FAILED after retries "
                  f"(cross-run attempt {retry_count}/{MAX_SCHEDULED_RETRIES}) — {e}")
            entry["status"] = "failed"
            entry["error"] = str(e)
            entry["scheduled_retry_count"] = retry_count
            had_failure = True
        changed = True

    if changed:
        save_schedule(entries)
        print("schedule.json updated.")
    else:
        print("No posts due.")

    if had_failure:
        sys.exit(1)


if __name__ == "__main__":
    main()