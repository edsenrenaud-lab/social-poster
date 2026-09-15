"""
One-off manual test for post_carousel() on Instagram and TikTok.

Run this directly (python3 test_carousel.py) from inside your social-poster
folder — it does NOT touch schedule.json and does NOT go through the
scheduler's retry/status-tracking logic. It just calls each platform's
post_carousel() once, straight, and prints exactly what comes back.

Before running: paste your real raw GitHub URLs into TEST_IMAGE_URLS below,
and make sure IG_USER_ID, IG_ACCESS_TOKEN, TIKTOK_CLIENT_KEY,
TIKTOK_CLIENT_SECRET, and TIKTOK_REFRESH_TOKEN are set as environment
variables in this Terminal session first.

Reminder: Instagram has no draft mode — a successful post_carousel() call
publishes live immediately. TikTok's lands as a private (SELF_ONLY) draft
in your inbox, same as your existing single-photo path.
"""

from platforms import instagram, tiktok

# Paste your 2-3 real raw GitHub URLs here, in the order you want them to
# appear in the carousel.
TEST_IMAGE_URLS = [
    "https://raw.githubusercontent.com/edsenrenaud-lab/social-poster/main/Media/tcwa/test1.jpg",
    "https://raw.githubusercontent.com/edsenrenaud-lab/social-poster/main/Media/tcwa/test2.jpg",
    "https://raw.githubusercontent.com/edsenrenaud-lab/social-poster/main/Media/tcwa/test3.jpg"
]

TEST_CAPTION = "Testing carousel posting — link in bio."


def test_instagram():
    print("\n--- Instagram carousel test ---")
    try:
        result = instagram.post_carousel(TEST_CAPTION, TEST_IMAGE_URLS)
        print(f"SUCCESS — Instagram post id: {result.get('id', '(no id returned)')}")
    except Exception as e:
        print(f"FAILED: {e}")


def test_tiktok():
    print("\n--- TikTok carousel test ---")
    try:
        result = tiktok.post_carousel(TEST_CAPTION, TEST_IMAGE_URLS)
        print(f"SUCCESS — TikTok publish_id: {result.get('id', '(no id returned)')} "
              f"(check your TikTok inbox for the draft)")
    except Exception as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    if "test1.jpg" in TEST_IMAGE_URLS[0]:
        print("Edit TEST_IMAGE_URLS at the top of this file with your real raw GitHub URLs first, "
              "then run this again.")
    else:
        test_instagram()
        test_tiktok()
