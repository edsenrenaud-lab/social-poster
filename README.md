# Social Media Scheduler

A free, self-hosted scheduler that posts to your Facebook Page and Instagram
Business account on a schedule you set. Runs on GitHub Actions (free) so it
works even when your computer is off. Pinterest is stubbed in for later.

## How it works

1. You list your posts in `schedule.json` — platform, caption, image, and
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
  "status": "pending"
}
```

Notes:
- `datetime` is in UTC (the trailing `Z` matters).
- `media_url` is optional for Facebook (text-only posts work) but
  required for Instagram, and must be a publicly reachable image URL.
- Commit and push the updated `schedule.json` — the next hourly run will
  pick it up.

## Checking on things

- Each run's logs are visible under the Actions tab in this repo.
- `schedule.json` is the source of truth — `posted` entries get a
  `posted_at` timestamp and post ID; `failed` entries get an `error` field.
