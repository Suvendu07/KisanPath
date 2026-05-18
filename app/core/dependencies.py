from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_token
from app.models.user_model import User

# Cookie names — defined once here so they never go out of sync
ACCESS_TOKEN_COOKIE  = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Please log in.",
    )

    # Step 1 — Read access token cookie
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise credentials_exception

    # Step 2 — Decode the token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Step 3 — Make sure it's an access token (not a refresh token)
    if payload.get("type") != "access":
        raise credentials_exception

    # Step 4 — Extract user id
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Step 5 — Fetch user from DB
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    # Step 6 — Check account is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support.",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Alias — same as get_current_user, reads more clearly in route code."""
    return current_user