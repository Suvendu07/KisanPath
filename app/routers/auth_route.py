from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.core.dependencies import (
    get_current_user,
    ACCESS_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
)
from app.core.security import decode_token, create_access_token
from app.models.user_model import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    AccessTokenResponse,
    UserResponse,
)
from app.services.auth_service import register_user, login_user

router = APIRouter()


ACCESS_MAX_AGE  = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60   # seconds
REFRESH_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds

# Set secure=True in production (requires HTTPS)
COOKIE_SECURE   = not settings.DEBUG


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Helper — attaches both tokens as HTTP-only cookies to the response."""
    response.set_cookie(
        key      = ACCESS_TOKEN_COOKIE,
        value    = access_token,
        httponly = True,             # JS cannot read this cookie
        samesite = "lax",            # protects against CSRF
        secure   = COOKIE_SECURE,    # HTTPS only in production
        max_age  = ACCESS_MAX_AGE,
    )
    response.set_cookie(
        key      = REFRESH_TOKEN_COOKIE,
        value    = refresh_token,
        httponly = True,
        samesite = "lax",
        secure   = COOKIE_SECURE,
        max_age  = REFRESH_MAX_AGE,
    )


def clear_auth_cookies(response: Response):
    """Helper — removes both token cookies (used on logout)."""
    response.delete_cookie(ACCESS_TOKEN_COOKIE,  samesite="lax")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, samesite="lax")



@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    user = register_user(data, db)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login — tokens are stored in HTTP-only cookies",
)
def login(
    data:     LoginRequest,
    response: Response,
    db:       Session = Depends(get_db),
):

    result = login_user(data, db)

    # Get the raw tokens from the service result to put in cookies
    # We call the service's internal token builders here
    from app.core.security import create_access_token, create_refresh_token
    token_data = {"sub": str(result.user_id), "role": result.role}

    set_auth_cookies(
        response,
        access_token  = create_access_token(token_data),
        refresh_token = create_refresh_token(token_data),
    )

    return result


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token using the refresh cookie",
)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token. Please log in again.",
    )

    # Read refresh token from cookie
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not refresh_token:
        raise credentials_exception

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise credentials_exception

    # Issue new access token cookie only
    new_access_token = create_access_token({
        "sub":  str(user.id),
        "role": user.role,
    })

    response.set_cookie(
        key      = ACCESS_TOKEN_COOKIE,
        value    = new_access_token,
        httponly = True,
        samesite = "lax",
        secure   = COOKIE_SECURE,
        max_age  = ACCESS_MAX_AGE,
    )

    return AccessTokenResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current logged-in user's profile",
)
def get_me(current_user: User = Depends(get_current_user)):

    return current_user


@router.post(
    "/logout",
    summary="Logout — clears both token cookies",
)
def logout(response: Response):

    clear_auth_cookies(response)
    return {"message": "Logged out successfully."}