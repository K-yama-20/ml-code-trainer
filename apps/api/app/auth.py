import hashlib
import secrets
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .config import settings
from .db import Profile, UserSettings, db_session

DEFAULT_SETTINGS = {
    "theme": "dark",
    "font_size": 14,
    "daily_goal": 20,
    "timezone": "Asia/Tokyo",
    "display_name": "Learner",
}
jwks = (
    jwt.PyJWKClient(settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json")
    if settings.supabase_url
    else None
)


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_local_guest(db):
    token = secrets.token_urlsafe(48)
    user = Profile(token_hash=token_hash(token))
    db.add(user)
    db.flush()
    db.add(UserSettings(user_id=user.id, data=DEFAULT_SETTINGS.copy()))
    db.commit()
    return user, token


def current_user(request: Request, db: Session = Depends(db_session)):
    if jwks:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(401, "Authentication required")
        token = header[7:]
        try:
            key = jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=["ES256", "RS256"],
                audience=settings.supabase_audience,
                issuer=settings.supabase_url.rstrip("/") + "/auth/v1",
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
            )
            import uuid

            user_id = str(uuid.UUID(claims["sub"]))
        except Exception:
            raise HTTPException(401, "Invalid or expired authentication token")
        user = db.get(Profile, user_id)
        if not user:
            user = Profile(id=user_id, display_name=claims.get("user_metadata", {}).get("display_name", "Learner")[:60])
            db.add(user)
            db.add(UserSettings(user_id=user_id, data=DEFAULT_SETTINGS.copy()))
            db.commit()
        return user
    cookie = request.cookies.get("trainer_guest", "")
    user = db.query(Profile).filter_by(token_hash=token_hash(cookie)).first() if cookie else None
    if not user:
        raise HTTPException(401, "Start a guest session first")
    return user
