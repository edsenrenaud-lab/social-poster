"""
Reads schedule.json, finds posts that are due, publishes them to the
right platform, and updates their status in place.

Run this on a schedule (see .github/workflows/scheduler.yml) — each run
checks for anything due since the last run and posts it.
"""

import json
import sys
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


def load_schedule() -> list:
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)


def save_schedule(entries: list) -> None:
    with open(SCHEDULE_PATH, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")


def is_due(entry: dict, now: datetime) -> bool:
    if entry.get("status") != "pending":
        return False
    scheduled_time = datetime.fromisoformat(entry["datetime"].replace("Z", "+00:00"))
    return scheduled_time <= now


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
            result = handler(entry.get("caption", ""), entry.get("media_url", ""))
            entry["status"] = "posted"
            entry["posted_at"] = now.isoformat()
            entry["result_id"] = result.get("id", "")
            print(f"[{entry['id']}] Success — {platform} post ID {entry['result_id']}")
        except Exception as e:
            print(f"[{entry['id']}] FAILED — {e}")
            entry["status"] = "failed"
            entry["error"] = str(e)
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
    
