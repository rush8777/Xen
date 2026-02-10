from __future__ import annotations

from dataclasses import dataclass
import os
import logging
from dotenv import load_dotenv

# Set up logging for config
logger = logging.getLogger(__name__)

# Load .env file from the same directory as this config.py
env_path = os.path.join(os.path.dirname(__file__), '.env')
logger.info(f"Loading .env from: {env_path}")
logger.info(f".env file exists: {os.path.exists(env_path)}")

# Use override=True so edits to backend/.env take effect after restart even if
# the process environment has old/empty values.
load_dotenv(env_path, override=True)

# Debug: Check if environment variables are loaded
youtube_client_id = os.getenv("YOUTUBE_CLIENT_ID")
youtube_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
facebook_client_id = os.getenv("FACEBOOK_CLIENT_ID")
facebook_client_secret = os.getenv("FACEBOOK_CLIENT_SECRET")
instagram_client_id = os.getenv("INSTAGRAM_CLIENT_ID")
instagram_client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET")
backend_base_url = os.getenv("BACKEND_BASE_URL")
logger.info(f"YOUTUBE_CLIENT_ID loaded: {bool(youtube_client_id)}")
logger.info(f"YOUTUBE_CLIENT_SECRET loaded: {bool(youtube_client_secret)}")
logger.info(f"FACEBOOK_CLIENT_ID loaded: {bool(facebook_client_id)}")
logger.info(f"FACEBOOK_CLIENT_SECRET loaded: {bool(facebook_client_secret)}")
logger.info(f"INSTAGRAM_CLIENT_ID loaded: {bool(instagram_client_id)}")
logger.info(f"INSTAGRAM_CLIENT_SECRET loaded: {bool(instagram_client_secret)}")
logger.info(f"BACKEND_BASE_URL loaded: {backend_base_url}")
if youtube_client_id:
    logger.info(f"YOUTUBE_CLIENT_ID (first 10): {youtube_client_id[:10]}...")


@dataclass
class OAuthProviderConfig:
    authorize_url: str
    token_url: str
    scope: str
    extra_auth_params: dict[str, str] | None = None


@dataclass
class Settings:
    """
    Simple settings loader backed by environment variables.

    This avoids pulling in heavier dependencies while still keeping
    configuration in one place.
    """

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    FRONTEND_BASE_URL: str = os.getenv(
        "FRONTEND_BASE_URL",
        "http://localhost:3000",
    )

    # Google / YouTube
    YOUTUBE_CLIENT_ID: str | None = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET: str | None = os.getenv("YOUTUBE_CLIENT_SECRET")
    YOUTUBE_REDIRECT_PATH: str = os.getenv(
        "YOUTUBE_REDIRECT_PATH",
        "/oauth/youtube/callback",
    )

    # Facebook
    FACEBOOK_CLIENT_ID: str | None = os.getenv("FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET: str | None = os.getenv("FACEBOOK_CLIENT_SECRET")
    FACEBOOK_REDIRECT_PATH: str = os.getenv(
        "FACEBOOK_REDIRECT_PATH",
        "/oauth/facebook/callback",
    )

    # Instagram (via Facebook)
    INSTAGRAM_CLIENT_ID: str | None = os.getenv("INSTAGRAM_CLIENT_ID")
    INSTAGRAM_CLIENT_SECRET: str | None = os.getenv("INSTAGRAM_CLIENT_SECRET")
    INSTAGRAM_REDIRECT_PATH: str = os.getenv(
        "INSTAGRAM_REDIRECT_PATH",
        "/oauth/instagram/callback",
    )

    # Twitter (X) - OAuth 2.0
    TWITTER_CLIENT_ID: str | None = os.getenv("TWITTER_CLIENT_ID")
    TWITTER_CLIENT_SECRET: str | None = os.getenv("TWITTER_CLIENT_SECRET")
    TWITTER_REDIRECT_PATH: str = os.getenv(
        "TWITTER_REDIRECT_PATH",
        "/oauth/twitter/callback",
    )

    # TikTok
    TIKTOK_CLIENT_KEY: str | None = os.getenv("TIKTOK_CLIENT_KEY")
    TIKTOK_CLIENT_SECRET: str | None = os.getenv("TIKTOK_CLIENT_SECRET")
    TIKTOK_REDIRECT_PATH: str = os.getenv(
        "TIKTOK_REDIRECT_PATH",
        "/oauth/tiktok/callback",
    )

    @property
    def providers(self) -> dict[str, OAuthProviderConfig]:
        """
        Static definition of provider endpoints and scopes.
        Credentials & redirect URIs are read from the fields above.
        """
        return {
            "youtube": OAuthProviderConfig(
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scope="https://www.googleapis.com/auth/youtube.readonly",
                extra_auth_params={
                    "access_type": "offline",
                    "include_granted_scopes": "true",
                    "prompt": "consent",
                },
            ),
            "facebook": OAuthProviderConfig(
                authorize_url="https://www.facebook.com/v20.0/dialog/oauth",
                token_url="https://graph.facebook.com/v20.0/oauth/access_token",
                scope="public_profile,email,pages_show_list,pages_read_engagement",
            ),
            "instagram": OAuthProviderConfig(
                authorize_url="https://www.facebook.com/v20.0/dialog/oauth",
                token_url="https://graph.facebook.com/v20.0/oauth/access_token",
                scope="instagram_basic,instagram_manage_insights,pages_show_list",
            ),
            "twitter": OAuthProviderConfig(
                authorize_url="https://twitter.com/i/oauth2/authorize",
                token_url="https://api.twitter.com/2/oauth2/token",
                scope="tweet.read users.read offline.access",
            ),
            "tiktok": OAuthProviderConfig(
                authorize_url="https://www.tiktok.com/v2/auth/authorize/",
                token_url="https://open.tiktokapis.com/v2/oauth/token/",
                scope="user.info.basic video.list",
            ),
        }


settings = Settings()


