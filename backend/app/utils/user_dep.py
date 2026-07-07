import os
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import AUTH_COOKIE_NAME, decode_session_token


PUBLIC_WORKSPACE_EMAIL = os.getenv("LUCEON_PUBLIC_WORKSPACE_EMAIL", "workspace@luceon.local")
PUBLIC_WORKSPACE_USER_ID = os.getenv("LUCEON_PUBLIC_WORKSPACE_USER_ID", "2")
PUBLIC_WORKSPACE_PASSWORD_HASH = "public-workspace-auth-disabled"


def auth_disabled() -> bool:
    return os.getenv("LUCEON_AUTH_DISABLED", "true").lower() not in {"0", "false", "no", "off"}


def get_or_create_public_user(db: Session) -> User:
    public_id: int | None = None
    try:
        public_id = int(PUBLIC_WORKSPACE_USER_ID)
    except (TypeError, ValueError):
        public_id = None

    user = db.query(User).filter(User.id == public_id).first() if public_id else None
    if user:
        return user

    user = db.query(User).filter(User.email == PUBLIC_WORKSPACE_EMAIL).first()
    if user:
        return user

    values = {
        "email": PUBLIC_WORKSPACE_EMAIL,
        "password_hash": PUBLIC_WORKSPACE_PASSWORD_HASH,
    }
    if public_id:
        values["id"] = public_id
    user = User(**values)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _legacy_header_enabled() -> bool:
    return os.getenv("AUTH_ALLOW_USER_HEADER", "false").lower() == "true"


async def get_current_user(
    session_token: Optional[str] = Cookie(None, alias=AUTH_COOKIE_NAME),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if auth_disabled():
        return get_or_create_public_user(db)

    token = session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    payload = decode_session_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="登录状态无效")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="登录状态无效")
    return user


async def get_user_id(
    x_user_id: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None, alias=AUTH_COOKIE_NAME),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> str:
    if x_user_id and _legacy_header_enabled():
        return x_user_id

    if auth_disabled():
        return str(get_or_create_public_user(db).id)

    current_user = await get_current_user(
        session_token=session_token,
        authorization=authorization,
        db=db,
    )
    return str(current_user.id)
