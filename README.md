# Social Media Scheduler

A free, self-hosted scheduler that posts to your Facebook Page, Instagram
Business account, and TikTok on a schedule you set. Runs on GitHub Actions
(free) so it works even when your computer is off. Pinterest is wired up
and will activate as soon as your trial access is approved.

## Supported media by platform

| Platform  | Image | Video | Text-only |
|-----------|:-----:|:-----:|:---------:|
| Facebook  | ✅ | ✅ | ✅ |
| Instagram | ✅ | ✅ (Reels) | ❌ (Instagram requires media) |
| TikTok    | ✅ (draft, unverified — see `tiktok.py`) | ✅ (draft, tested live) | ❌ |
| Pinterest | ✅ (pending trial access) | ✅ (pending trial access) | ❌ (Pinterest requires media) |

TikTok and Pinterest post as **drafts** — they land ready-to-go and need
one manual tap to publish, since full silent auto-publish requires a
platform app audit neither has gone through yet.

## How it works

1. You list your posts in `schedule.json` — platform, caption, media, and
   the time to post.
2. A GitHub Actions workflow runs every hour, checks for anything due, and
   publishes it via each platform's official API.
3. The schedule file gets updated in place (`pending` → `posted`/`failed`)
   so you always have a record of what went out and when.

## Adding posts

Edit `schedule.json` and add entries in this format:

```json
{
  "id": "unique-name-for-this-post",
  "platform": "facebook",
  "datetime": "2026-08-15T14:00:00Z",
  "caption": "Your post text here",
  "media_url": "",
  "media_type": "",
  "status": "pending"
}
```

Notes:
- `datetime` is in UTC (the trailing `Z` matters).
- `media_url` is optional for Facebook (text-only posts work) but
  required for Instagram, TikTok, and Pinterest, and must be a publicly
  reachable URL (the GitHub raw-file pattern already in use works for all
  of them).
- `media_type` is optional — leave it `""` and the scheduler will detect
  image vs. video from the file extension in `media_url` (`.jpg/.png/...`
  vs. `.mp4/.mov/...`). Only set it explicitly if you're using a URL
  without a normal file extension.
- Commit and push the updated `schedule.json` — the next hourly run will
  pick it up.

## Checking on things

- Each run's logs are visible under the Actions tab in this repo.
- `schedule.json` is the source of truth — `posted` entries get a
  `posted_at` timestamp and post ID; `failed` entries get an `error` field.

## Before trusting a new media type in the live schedule

- **Facebook video, Instagram video (Reels):** implemented against Meta's
  documented Graph API endpoints, not yet run against a live post — do one
  test post on each before relying on it for a real launch day.
- **TikTok photo:** implemented but unverified — TikTok's photo Content
  Posting API is newer than their video API. Test before trusting.
- **Pinterest (image or video):** implemented but can't be tested until
  trial access is approved. Test both once access comes through.
