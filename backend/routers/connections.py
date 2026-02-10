from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_db
from ..models import OAuthConnection, User


router = APIRouter(prefix="/api", tags=["connections"])


class ConnectionOut(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    color: str
    connected: bool
    contactPerson: str | None = None


BASE_APPS: list[ConnectionOut] = [
    ConnectionOut(
        id="youtube",
        name="YouTube",
        description="Connect and manage your YouTube channel",
        icon="▶️",
        color="bg-red-500 dark:bg-red-600",
        connected=False,
        contactPerson="You",
    ),
    ConnectionOut(
        id="facebook",
        name="Facebook",
        description="Integrate with your Facebook business page",
        icon="f",
        color="bg-blue-600 dark:bg-blue-700",
        connected=False,
        contactPerson="Marketing Team",
    ),
    ConnectionOut(
        id="instagram",
        name="Instagram",
        description="Connect your Instagram profile for insights",
        icon="📷",
        color="bg-pink-500 dark:bg-pink-600",
        connected=False,
        contactPerson="Social Media Manager",
    ),
    ConnectionOut(
        id="twitter",
        name="Twitter",
        description="Manage your Twitter account and engagement",
        icon="𝕏",
        color="bg-black dark:bg-zinc-700",
        connected=False,
        contactPerson="Community Manager",
    ),
    ConnectionOut(
        id="tiktok",
        name="TikTok",
        description="Connect your TikTok account for video content",
        icon="🎵",
        color="bg-black dark:bg-zinc-800",
        connected=False,
        contactPerson="Content Creator",
    ),
]


def _get_or_create_user(db: Session) -> User:
    # TODO: Replace with real authenticated user from your auth system.
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email=None, name=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/connections", response_model=List[ConnectionOut])
def list_connections(db: Session = Depends(get_db)) -> list[ConnectionOut]:
    user = _get_or_create_user(db)
    conns = {
        c.provider: c
        for c in db.query(OAuthConnection)
        .filter(OAuthConnection.user_id == user.id)
        .all()
    }

    result: list[ConnectionOut] = []
    for base in BASE_APPS:
        connected = base.id in conns
        result.append(
            ConnectionOut(
                **base.dict(exclude={"connected"}),
                connected=connected,
            )
        )
    return result


@router.post("/connections/{provider}/disconnect")
def disconnect(provider: str, db: Session = Depends(get_db)) -> dict:
    provider = provider.lower()
    if provider not in settings.providers:
        return {"status": "error", "message": "Unknown provider"}

    user = _get_or_create_user(db)
    conn = (
        db.query(OAuthConnection)
        .filter(
            OAuthConnection.user_id == user.id,
            OAuthConnection.provider == provider,
        )
        .first()
    )
    if conn:
        db.delete(conn)
        db.commit()

    return {"status": "ok"}


