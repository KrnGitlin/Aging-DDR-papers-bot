from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import tweepy


def main() -> int:
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    missing = [
        k for k, v in (
            ("TWITTER_API_KEY", api_key),
            ("TWITTER_API_SECRET", api_secret),
            ("TWITTER_ACCESS_TOKEN", access_token),
            ("TWITTER_ACCESS_TOKEN_SECRET", access_token_secret),
        ) if not v
    ]
    if missing:
        print("Missing env vars:", ", ".join(missing))
        print("Load them via .env or set in your shell and re-run.")
        return 1

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api = tweepy.API(auth)
    user = api.verify_credentials()
    if not user:
        print("Failed to verify credentials")
        return 2
    print(f"Authenticated as @{getattr(user, 'screen_name', 'unknown')} (id={getattr(user, 'id', '?')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
