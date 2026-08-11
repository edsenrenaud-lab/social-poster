"""
Placeholder for Pinterest posting.

Pinterest's API requires a free developer app and board ID. When you're
ready to add this platform:
  1. Register at https://developers.pinterest.com
  2. Create an app, get it approved for the "pins:write" scope
  3. Get your board ID from the Pinterest API or your board's URL
  4. Fill in the post() function below using their /v5/pins endpoint

Required environment variables (once implemented):
  PINTEREST_ACCESS_TOKEN
  PINTEREST_BOARD_ID
"""


def post(caption: str, media_url: str = "") -> dict:
    raise NotImplementedError(
        "Pinterest posting isn't wired up yet. See the comments in this file "
        "to add it when you're ready."
    )
