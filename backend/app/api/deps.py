import uuid
from fastapi import Header, HTTPException, Depends, status
from typing import Optional
import jwt
try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

class CurrentUser:
    def __init__(self, user_id: str, email: Optional[str] = None):
        self.id = user_id
        self.email = email

def validate_uuid(val: Optional[str]) -> bool:
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> CurrentUser:
    """
    Validates Authorization header (Bearer token) and derives authenticated user ID from token sub.
    If x-user-id header is provided, verifies that it matches the verified JWT user ID.
    Validates that user_id is a valid UUID string to prevent database syntax errors.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.replace("Bearer ", "").strip()
    try:
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        else:
            payload = jwt.decode(token, options={"verify_signature": False})

        token_user_id = payload.get("sub") or payload.get("user_id")
        email = payload.get("email")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )

    if not token_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token contains no valid user identity (sub)"
        )

    if x_user_id and x_user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security violation: x-user-id header does not match verified JWT identity"
        )

    target_user_id = token_user_id

    if not validate_uuid(target_user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user identity format: '{target_user_id}' is not a valid UUID"
        )

    return CurrentUser(user_id=target_user_id, email=email)


