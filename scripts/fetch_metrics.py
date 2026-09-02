"""
Reads schedule.json, finds posts that have been live for at least 24
hours, fetches current engagement metrics for each from its platform,
and appends a timestamped snapshot to metrics.json.

Run daily (see .github/workflows/metrics.yml). Because it appends rather
than overwrites, metrics.json builds a time series per post — so you can
see a post's engagement grow over the campaign, not just its metrics at
one moment.

24-hour wait is intentional: platforms under-report engagement in the
first few hours, and TikTok drafts specifically need time for you to
manually approve them before they're live at all.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from platforms import facebook, instagram, tiktok

SCHEDULE_PATH = Path(__file__).parent.parent / "schedule.json"
METRICS_PATH = Path(__file__).parent.parent / "metrics.json"

MIN_AGE_HOURS = 24

# Pinterest omitted until it's live — add pinterest.get_insights here once
# the trial API access comes through and pinterest.py has one.
INSIGHTS_HANDLERS = {
    "facebook": lambda entry: facebook.get_insights(entry["result_id"]),
    "instagram": lambda entry: instagram.get_insights(entry["result_id"], entry.get("media_type", "")),
    "tiktok": lambda entry: tiktok.get_insights(entry["result_id"]),
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def is_ready_for_metrics(entry: dict, now: datetime) -> bool:
    if entry.get("status") != "posted" or not entry.get("result_id"):
        return False
    posted_at = datetime.fromisoformat(entry["posted_at"].replace("Z", "+00:00"))
    age_hours = (now - posted_at).total_seconds() / 3600
    return age_hours >= MIN_AGE_HOURS


def main() -> None:
    now = datetime.now(timezone.utc)
    entries = load_json(SCHEDULE_PATH, [])
    history = load_json(METRICS_PATH, [])
    had_failure = False
    fetched_count = 0

    for entry in entries:
        if not is_ready_for_metrics(entry, now):
            continue

        platform = entry.get("platform")
        handler = INSIGHTS_HANDLERS.get(platform)
        if handler is None:
            continue  # platform not wired for metrics yet (e.g. Pinterest)

        try:
            metrics = handler(entry)
            if metrics.get("status") == "not_published":
                print(f"[{entry['id']}] {platform} draft not yet approved — skipping")
                continue

            history.append({
                "entry_id": entry["id"],
                "platform": platform,
                "result_id": entry["result_id"],
                "fetched_at": now.isoformat(),
                "metrics": metrics,
            })
            fetched_count += 1
            print(f"[{entry['id']}] {platform} metrics: {metrics}")
        except Exception as e:
            print(f"[{entry['id']}] Metrics fetch FAILED — {e}")
            had_failure = True

    if fetched_count:
        save_json(METRICS_PATH, history)
        print(f"metrics.json updated with {fetched_count} new snapshot(s).")
    else:
        print("No new metrics fetched this run.")

    if had_failure:
        sys.exit(1)


if __name__ == "__main__":
    main()
