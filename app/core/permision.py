from fastapi import Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.models.user_model import User, UserRole


def require_roles(allowed_roles: list[str]):

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}."
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only ADMIN can pass."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required."
        )
    return current_user


def require_farmer(current_user: User = Depends(get_current_user)) -> User:
    """Only FARMER can pass."""
    if current_user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmer access required."
        )
    return current_user


def require_vendor(current_user: User = Depends(get_current_user)) -> User:
    """Only VENDOR can pass."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor access required."
        )
    return current_user


def require_user(current_user: User = Depends(get_current_user)) -> User:
    """Only regular USER (buyer) can pass."""
    if current_user.role != UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User (buyer) access required."
        )
    return current_user


def require_admin_or_farmer(current_user: User = Depends(get_current_user)) -> User:
    """ADMIN or FARMER can pass."""
    if current_user.role not in [UserRole.ADMIN, UserRole.FARMER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Farmer access required."
        )
    return current_user