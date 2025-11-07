from __future__ import annotations

import os
from typing import Optional

import tweepy
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class TwitterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ) -> None:
        api_key = api_key or os.getenv("TWITTER_API_KEY")
        api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise RuntimeError(
                "Twitter credentials missing. Set TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET."
            )

        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def verify(self) -> str:
        user = self.api.verify_credentials()
        return getattr(user, "screen_name", "unknown")

    def post(self, text: str) -> None:
        if not text:
            return
        if len(text) > 280:
            text = text[:277] + "..."
        self.api.update_status(status=text)
