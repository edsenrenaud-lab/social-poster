"""
Checks every pending entry in schedule.json to confirm its media_url is
actually reachable, WITHOUT posting anything anywhere. Run this whenever
schedule.json changes, and on a light daily schedule, to catch broken
media links days before they'd actually fail a real post.

This is exactly the kind of check that would have caught the Jpeg/
subfolder move and the Day 7 broken-link incident in advance, instead
of finding out at post time.

Exits with code 1 (failing the job) if any pending entry's media_url
returns a non-200 response, so the same failure-notification pipeline
used by poster.py can alert on this too.
"""

import json
import sys
from pathlib import Path

import requests

SCHEDULE_PATH = Path(__file__).parent.parent / "schedule.json"

# Platforms that require media — an empty media_url is only valid for
# Facebook and Threads text-only posts, so don't flag those as broken.
REQUIRES_MEDIA = {"instagram", "tiktok", "pinterest"}


def load_schedule() -> list:
    with open(SCHEDULE_PATH, "r") as f:
        return json.load(f)


def check_url(url: str) -> tuple:
    """Returns (ok: bool, detail: str)."""
    try:
        response = requests.head(url, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            return True, "OK"
        return False, f"HTTP {response.status_code}"
    except requests.RequestException as e:
        return False, f"Request failed: {e}"


def main() -> None:
    entries = load_schedule()
    pending = [e for e in entries if e.get("status") == "pending"]

    print(f"Checking {len(pending)} pending entries...")

    broken = []
    for entry in pending:
        media_url = entry.get("media_url", "")
        platform = entry.get("platform", "")

        if not media_url:
            if platform in REQUIRES_MEDIA:
                broken.append((entry["id"], "", f"{platform} requires media but media_url is empty"))
            continue

        ok, detail = check_url(media_url)
        status_label = "OK" if ok else "BROKEN"
        print(f"  [{status_label}] {entry['id']} -> {media_url} ({detail})")

        if not ok:
            broken.append((entry["id"], media_url, detail))

    print()
    if broken:
        print(f"{len(broken)} BROKEN media link(s) found:")
        for entry_id, url, detail in broken:
            print(f"  - {entry_id}: {url or '(no url)'} — {detail}")
        sys.exit(1)
    else:
        print("All pending media links are reachable.")


if __name__ == "__main__":
    main()
