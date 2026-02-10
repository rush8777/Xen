from __future__ import annotations

from datetime import datetime, timedelta
import secrets
import logging
import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import OAuthConnection, OAuthState, User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/oauth", tags=["oauth"])


def _create_oauth_state(db: Session, provider: str, state: str) -> None:
    """Store OAuth state in database"""
    oauth_state = OAuthState(
        state=state,
        provider=provider,
        expires_at=datetime.utcnow() + timedelta(minutes=10)  # State expires in 10 minutes
    )
    db.add(oauth_state)
    db.commit()


def _verify_oauth_state(db: Session, provider: str, state: str) -> bool:
    """Verify and consume OAuth state"""
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.provider == provider,
        OAuthState.expires_at > datetime.utcnow()
    ).first()
    
    if oauth_state:
        # Delete the used state
        db.delete(oauth_state)
        db.commit()
        return True
    return False


def _build_redirect_uri(provider: str) -> str:
    base = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    # The backend callback URL is served by FastAPI; providers must be
    # configured to call back to this URL.
    return f"{base}{_callback_path_for_provider(provider)}"


def _callback_path_for_provider(provider: str) -> str:
    mapping = {
        "youtube": settings.YOUTUBE_REDIRECT_PATH,
        "facebook": settings.FACEBOOK_REDIRECT_PATH,
        "instagram": settings.INSTAGRAM_REDIRECT_PATH,
        "twitter": settings.TWITTER_REDIRECT_PATH,
        "tiktok": settings.TIKTOK_REDIRECT_PATH,
    }
    return mapping[provider]


def _client_credentials_for_provider(provider: str) -> tuple[str, str]:
    logger.info(f"=== Getting client credentials for provider: {provider} ===")
    
    if provider == "youtube":
        cid = settings.YOUTUBE_CLIENT_ID
        secret = settings.YOUTUBE_CLIENT_SECRET
        logger.info(f"YouTube - Client ID exists: {bool(cid)}")
        logger.info(f"YouTube - Client Secret exists: {bool(secret)}")
        if cid:
            logger.info(f"YouTube - Client ID (first 10): {cid[:10]}...")
    elif provider == "facebook":
        cid = settings.FACEBOOK_CLIENT_ID
        secret = settings.FACEBOOK_CLIENT_SECRET
        logger.info(f"Facebook - Client ID exists: {bool(cid)}")
        logger.info(f"Facebook - Client Secret exists: {bool(secret)}")
    elif provider == "instagram":
        cid = settings.INSTAGRAM_CLIENT_ID
        secret = settings.INSTAGRAM_CLIENT_SECRET
        logger.info(f"Instagram - Client ID exists: {bool(cid)}")
        logger.info(f"Instagram - Client Secret exists: {bool(secret)}")
    elif provider == "twitter":
        cid = settings.TWITTER_CLIENT_ID
        secret = settings.TWITTER_CLIENT_SECRET
        logger.info(f"Twitter - Client ID exists: {bool(cid)}")
        logger.info(f"Twitter - Client Secret exists: {bool(secret)}")
    elif provider == "tiktok":
        cid = settings.TIKTOK_CLIENT_KEY
        secret = settings.TIKTOK_CLIENT_SECRET
        logger.info(f"TikTok - Client Key exists: {bool(cid)}")
        logger.info(f"TikTok - Client Secret exists: {bool(secret)}")
    else:
        logger.error(f"Unsupported provider: {provider}")
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if not cid or not secret:
        logger.error(f"Client credentials not configured for provider '{provider}'")
        logger.error(f"Client ID is None: {cid is None}")
        logger.error(f"Client Secret is None: {secret is None}")
        raise HTTPException(
            status_code=500,
            detail=f"Client credentials not configured for provider '{provider}'",
        )
    
    logger.info(f"=== Successfully retrieved credentials for {provider} ===")
    return cid, secret


@router.get("/{provider}/authorize")
def authorize(provider: str, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    logger.info(f"=== OAuth Authorize Started for provider: {provider} ===")
    logger.info(f"Request URL: {request.url}")
    
    provider = provider.lower()
    logger.info(f"Normalized provider name: {provider}")
    
    provider_cfg = settings.providers.get(provider)
    logger.info(f"Provider config found: {provider_cfg is not None}")
    if provider_cfg:
        logger.info(f"Provider authorize_url: {provider_cfg.authorize_url}")
        logger.info(f"Provider token_url: {provider_cfg.token_url}")
        logger.info(f"Provider scope: {provider_cfg.scope}")
        logger.info(f"Provider extra_auth_params: {provider_cfg.extra_auth_params}")
    
    if not provider_cfg:
        logger.error(f"Unknown provider: {provider}")
        raise HTTPException(status_code=404, detail="Unknown provider")

    client_id, _ = _client_credentials_for_provider(provider)
    logger.info(f"Client ID (first 10 chars): {client_id[:10]}...")
    
    redirect_uri = _build_redirect_uri(provider)
    logger.info(f"Redirect URI: {redirect_uri}")

    state = secrets.token_urlsafe(32)
    logger.info(f"Generated state (first 20 chars): {state[:20]}...")

    # Store state in database instead of cookie
    _create_oauth_state(db, provider, state)
    logger.info(f"Stored OAuth state in database for provider: {provider}")

    params: Dict[str, Any] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": provider_cfg.scope,
        "state": state,
    }
    if provider_cfg.extra_auth_params:
        params.update(provider_cfg.extra_auth_params)

    if provider == "twitter":
        params["code_challenge"] = "plain_challenge"
        params["code_challenge_method"] = "plain"

    if provider == "tiktok":
        params["client_key"] = client_id

    logger.info(f"Authorization params (excluding sensitive): { {k: v for k, v in params.items() if k not in ['client_id', 'client_secret']} }")

    url = provider_cfg.authorize_url + "?" + "&".join(
        f"{key}={httpx.QueryParams({key: value})[key]}" for key, value in params.items()
    )

    logger.info(f"Generated authorization URL: {url}")
    logger.info(f"=== OAuth Authorize Completed for {provider} ===")

    return JSONResponse({"url": url})


@router.get("/{provider}/callback")
def callback(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    logger.info(f"=== OAuth Callback Started for provider: {provider} ===")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Query params: {dict(request.query_params)}")
    
    provider = provider.lower()
    logger.info(f"Normalized provider name: {provider}")
    
    provider_cfg = settings.providers.get(provider)
    logger.info(f"Provider config found: {provider_cfg is not None}")
    if provider_cfg:
        logger.info(f"Provider authorize_url: {provider_cfg.authorize_url}")
        logger.info(f"Provider token_url: {provider_cfg.token_url}")
        logger.info(f"Provider scope: {provider_cfg.scope}")
    
    if not provider_cfg:
        logger.error(f"Unknown provider: {provider}")
        raise HTTPException(status_code=404, detail="Unknown provider")

    if not state:
        logger.error("Missing OAuth state parameter")
        raise HTTPException(status_code=400, detail="Missing OAuth state")
    
    if not _verify_oauth_state(db, provider, state):
        logger.error(f"Invalid OAuth state: {state}")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    if not code:
        logger.error("Missing authorization code in request")
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    logger.info(f"Authorization code received (first 20 chars): {code[:20]}...")

    client_id, client_secret = _client_credentials_for_provider(provider)
    logger.info(f"Client ID (first 10 chars): {client_id[:10]}...")
    logger.info(f"Client secret exists: {bool(client_secret)}")
    
    redirect_uri = _build_redirect_uri(provider)
    logger.info(f"Redirect URI: {redirect_uri}")

    logger.info("=== Building token request data ===")
    token_data: Dict[str, Any] = {
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    if provider in ("youtube", "facebook", "instagram"):
        token_data["grant_type"] = "authorization_code"
    elif provider == "twitter":
        token_data["grant_type"] = "authorization_code"
    elif provider == "tiktok":
        token_data["grant_type"] = "authorization_code"
        token_data["client_key"] = client_id

    logger.info(f"Token request data (excluding secret): { {k: v for k, v in token_data.items() if k != 'client_secret'} }")

    logger.info("=== Making token request ===")
    with httpx.Client(timeout=10.0) as client:
        token_resp = client.post(provider_cfg.token_url, data=token_data)

    logger.info(f"Token response status: {token_resp.status_code}")
    logger.info(f"Token response headers: {dict(token_resp.headers)}")
    
    if token_resp.status_code != 200:
        logger.error(f"Token request failed. Status: {token_resp.status_code}")
        logger.error(f"Token response body: {token_resp.text}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to obtain access token from {provider}",
        )

    token_json = token_resp.json()
    logger.info(f"Token response JSON keys: {list(token_json.keys())}")
    access_token = token_json.get("access_token")
    refresh_token = token_json.get("refresh_token")
    expires_in = token_json.get("expires_in")

    logger.info(f"Access token exists: {bool(access_token)}")
    logger.info(f"Refresh token exists: {bool(refresh_token)}")
    logger.info(f"Expires in: {expires_in}")

    if not access_token:
        logger.error("No access token in response")
        raise HTTPException(
            status_code=400,
            detail="Provider did not return an access token",
        )

    expires_at: datetime | None = None
    if isinstance(expires_in, (int, float)):
        expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        logger.info(f"Token expires at: {expires_at}")

    provider_account_id: str | None = None
    display_name: str | None = None

    logger.info("=== Fetching user profile ===")
    with httpx.Client(timeout=10.0) as client:
        headers = {"Authorization": f"Bearer {access_token}"}

        if provider == "youtube":
            logger.info("Fetching YouTube user profile...")
            api_url = "https://www.googleapis.com/youtube/v3/channels"
            params = {"part": "snippet", "mine": "true"}
            logger.info(f"YouTube API URL: {api_url}")
            logger.info(f"YouTube API params: {params}")
            
            resp = client.get(api_url, params=params, headers=headers)
            logger.info(f"YouTube API response status: {resp.status_code}")
            logger.info(f"YouTube API response headers: {dict(resp.headers)}")
            
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"YouTube API response data: {data}")
                items = data.get("items") or []
                logger.info(f"YouTube API items count: {len(items)}")
                if items:
                    snippet = items[0].get("snippet") or {}
                    provider_account_id = items[0].get("id")
                    display_name = snippet.get("title")
                    logger.info(f"YouTube account ID: {provider_account_id}")
                    logger.info(f"YouTube display name: {display_name}")
            else:
                logger.error(f"YouTube API error response: {resp.text}")

        elif provider == "facebook":
            logger.info("Fetching Facebook user profile...")
            resp = client.get(
                "https://graph.facebook.com/v20.0/me",
                params={"fields": "id,name"},
                headers=headers,
            )
            logger.info(f"Facebook API response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                # Check for Graph API errors
                if "error" in data:
                    error_info = data.get("error", {})
                    logger.error(f"Facebook Graph API error: {error_info}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Facebook API error: {error_info.get('message', 'Unknown error')}",
                    )
                provider_account_id = data.get("id")
                display_name = data.get("name")
                logger.info(f"Facebook account ID: {provider_account_id}")
                logger.info(f"Facebook display name: {display_name}")
            else:
                logger.error(f"Facebook API error response: {resp.text}")
                try:
                    error_data = resp.json()
                    if "error" in error_data:
                        error_info = error_data.get("error", {})
                        raise HTTPException(
                            status_code=400,
                            detail=f"Facebook API error: {error_info.get('message', 'Unknown error')}",
                        )
                except Exception:
                    pass
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch Facebook user profile",
                )

        elif provider == "instagram":
            logger.info("Fetching Instagram user profile...")
            # First, get Facebook user info
            user_resp = client.get(
                "https://graph.facebook.com/v20.0/me",
                params={"fields": "id,name"},
                headers=headers,
            )
            logger.info(f"Facebook user API response status: {user_resp.status_code}")
            
            if user_resp.status_code != 200:
                logger.error(f"Failed to fetch Facebook user: {user_resp.text}")
                try:
                    error_data = user_resp.json()
                    if "error" in error_data:
                        error_info = error_data.get("error", {})
                        raise HTTPException(
                            status_code=400,
                            detail=f"Facebook API error: {error_info.get('message', 'Unknown error')}",
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch Facebook user profile",
                )
            
            user_data = user_resp.json()
            if "error" in user_data:
                error_info = user_data.get("error", {})
                logger.error(f"Facebook Graph API error: {error_info}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Facebook API error: {error_info.get('message', 'Unknown error')}",
                )
            
            facebook_user_id = user_data.get("id")
            logger.info(f"Facebook user ID: {facebook_user_id}")
            
            # Get user's Facebook Pages
            logger.info("Fetching Facebook Pages...")
            pages_resp = client.get(
                "https://graph.facebook.com/v20.0/me/accounts",
                params={"fields": "id,name,instagram_business_account"},
                headers=headers,
            )
            logger.info(f"Facebook Pages API response status: {pages_resp.status_code}")
            
            if pages_resp.status_code != 200:
                logger.error(f"Failed to fetch Facebook Pages: {pages_resp.text}")
                try:
                    error_data = pages_resp.json()
                    if "error" in error_data:
                        error_info = error_data.get("error", {})
                        raise HTTPException(
                            status_code=400,
                            detail=f"Facebook API error: {error_info.get('message', 'Unknown error')}",
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch Facebook Pages. Make sure you have a Facebook Page connected to an Instagram Business Account.",
                )
            
            pages_data = pages_resp.json()
            if "error" in pages_data:
                error_info = pages_data.get("error", {})
                logger.error(f"Facebook Graph API error: {error_info}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Facebook API error: {error_info.get('message', 'Unknown error')}",
                )
            
            pages = pages_data.get("data", [])
            logger.info(f"Found {len(pages)} Facebook Pages")
            
            # Find the first page with an Instagram Business Account
            instagram_account = None
            for page in pages:
                ig_account = page.get("instagram_business_account")
                if ig_account:
                    instagram_account = ig_account
                    logger.info(f"Found Instagram Business Account: {instagram_account.get('id')} on page: {page.get('name')}")
                    break
            
            if not instagram_account:
                logger.error("No Instagram Business Account found connected to any Facebook Page")
                raise HTTPException(
                    status_code=400,
                    detail="No Instagram Business Account found. Please connect an Instagram Business Account to a Facebook Page first.",
                )
            
            # Get Instagram account details
            ig_account_id = instagram_account.get("id")
            logger.info(f"Fetching Instagram Business Account details for ID: {ig_account_id}")
            
            ig_resp = client.get(
                f"https://graph.facebook.com/v20.0/{ig_account_id}",
                params={"fields": "id,username,name"},
                headers=headers,
            )
            logger.info(f"Instagram API response status: {ig_resp.status_code}")
            
            if ig_resp.status_code != 200:
                logger.error(f"Failed to fetch Instagram account: {ig_resp.text}")
                try:
                    error_data = ig_resp.json()
                    if "error" in error_data:
                        error_info = error_data.get("error", {})
                        raise HTTPException(
                            status_code=400,
                            detail=f"Instagram API error: {error_info.get('message', 'Unknown error')}",
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch Instagram Business Account details",
                )
            
            ig_data = ig_resp.json()
            if "error" in ig_data:
                error_info = ig_data.get("error", {})
                logger.error(f"Instagram Graph API error: {error_info}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Instagram API error: {error_info.get('message', 'Unknown error')}",
                )
            
            provider_account_id = ig_data.get("id")
            display_name = ig_data.get("name") or ig_data.get("username")
            logger.info(f"Instagram account ID: {provider_account_id}")
            logger.info(f"Instagram display name: {display_name}")

        elif provider == "twitter":
            logger.info("Fetching Twitter user profile...")
            resp = client.get(
                "https://api.twitter.com/2/users/me",
                headers=headers,
            )
            logger.info(f"Twitter API response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json().get("data") or {}
                provider_account_id = data.get("id")
                display_name = data.get("username")
                logger.info(f"Twitter account ID: {provider_account_id}")
                logger.info(f"Twitter username: {display_name}")

        elif provider == "tiktok":
            logger.info("Fetching TikTok user profile...")
            resp = client.get(
                "https://open.tiktokapis.com/v2/user/info/",
                params={"fields": "open_id,display_name"},
                headers=headers,
            )
            logger.info(f"TikTok API response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json().get("data") or {}
                user_obj = data.get("user") or {}
                provider_account_id = user_obj.get("open_id")
                display_name = user_obj.get("display_name")
                logger.info(f"TikTok account ID: {provider_account_id}")
                logger.info(f"TikTok display name: {display_name}")

    logger.info("=== Database operations ===")
    # TODO: Replace this with your real authenticated user ID, e.g. from JWT.
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        logger.info("Creating new user with ID 1")
        user = User(id=1, email=None, name=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        logger.info(f"Found existing user with ID: {user.id}")

    conn = (
        db.query(OAuthConnection)
        .filter(
            OAuthConnection.user_id == user.id,
            OAuthConnection.provider == provider,
        )
        .first()
    )

    scopes_str = provider_cfg.scope
    logger.info(f"Existing connection found: {conn is not None}")
    
    if conn:
        logger.info("Updating existing OAuth connection")
        conn.access_token = access_token
        conn.refresh_token = refresh_token
        conn.expires_at = expires_at
        conn.scopes = scopes_str
        conn.provider_account_id = provider_account_id
        conn.display_name = display_name
    else:
        logger.info("Creating new OAuth connection")
        conn = OAuthConnection(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            display_name=display_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=scopes_str,
        )
        db.add(conn)

    db.commit()
    logger.info("Database commit completed")

    redirect_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/connections?oauth_status=success&provider={provider}"
    logger.info(f"Redirecting to: {redirect_url}")
    logger.info(f"=== OAuth Callback Completed for {provider} ===")
    return RedirectResponse(url=redirect_url)


