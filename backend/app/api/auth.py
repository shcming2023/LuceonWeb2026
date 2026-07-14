from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import (
    clear_auth_cookie,
    create_session_token,
    hash_password,
    normalize_email,
    set_auth_cookie,
    validate_password,
    verify_password,
)
from app.utils.user_dep import auth_disabled, get_current_user, get_or_create_public_user, user_payload


router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


def _auth_response(response: Response, user: User) -> dict:
    set_auth_cookie(response, create_session_token(user))
    return {"user": user_payload(user)}


@router.post("/auth/register")
def register(payload: AuthRequest, response: Response, db: Session = Depends(get_db)):
    if auth_disabled():
        user = get_or_create_public_user(db)
        clear_auth_cookie(response)
        return {"user": user_payload(user), "auth_disabled": True}

    email = normalize_email(payload.email)
    password = validate_password(payload.password)

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="邮箱已注册")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_response(response, user)


@router.post("/auth/login")
def login(payload: AuthRequest, response: Response, db: Session = Depends(get_db)):
    if auth_disabled():
        user = get_or_create_public_user(db)
        clear_auth_cookie(response)
        return {"user": user_payload(user), "auth_disabled": True}

    email = normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    return _auth_response(response, user)


@router.post("/auth/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"msg": "已退出登录"}


@router.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return user_payload(current_user)
