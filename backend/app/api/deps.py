import uuid
from fastapi import Header, Query, HTTPException, Depends, status
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient, PyJWKClientError
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

# Cache PyJWKClient instances per JWKS URL
_jwk_clients: Dict[str, PyJWKClient] = {}

def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    if jwks_url not in _jwk_clients:
        _jwk_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True)
    return _jwk_clients[jwks_url]

ALLOWED_ASYMMETRIC_ALGORITHMS = {"ES256", "RS256"}
ALLOWED_SYMMETRIC_ALGORITHMS = {"HS256"}

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
) -> CurrentUser:
    """
    Validates Authorization header (Bearer token) or token query parameter and derives authenticated user ID from token sub.
    Supports asymmetric JWTs (ES256/RS256 via Supabase JWKS) and legacy symmetric JWTs (HS256).
    If x-user-id header is provided, verifies that it matches the verified JWT user ID.
    Validates that user_id is a valid UUID string to prevent database syntax errors.
    """
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.replace("Bearer ", "").strip()
    elif token and isinstance(token, str) and token.strip():
        auth_token = token.strip()

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header or token parameter"
        )

    try:
        header = jwt.get_unverified_header(auth_token)
        alg = header.get("alg")

        if not alg:
            raise ValueError("Token header missing 'alg' parameter")

        if alg in ALLOWED_ASYMMETRIC_ALGORITHMS:
            supabase_url = (getattr(settings, "SUPABASE_URL", "") or getattr(settings, "NEXT_PUBLIC_SUPABASE_URL", "")).strip()
            if not supabase_url:
                raise ValueError("Supabase URL is not configured for JWKS asymmetric token verification")

            jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            jwk_client = _get_jwk_client(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(auth_token)
            payload = jwt.decode(
                auth_token,
                signing_key.key,
                algorithms=[alg],
                audience="authenticated"
            )
        elif alg in ALLOWED_SYMMETRIC_ALGORITHMS:
            secret = getattr(settings, "SUPABASE_JWT_SECRET", "")
            if not secret:
                raise ValueError(f"{alg} algorithm requires SUPABASE_JWT_SECRET to be configured")
            payload = jwt.decode(
                auth_token,
                secret,
                algorithms=[alg],
                audience="authenticated"
            )
        else:
            raise ValueError(f"Unsupported or disallowed algorithm '{alg}'")


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

    if x_user_id and isinstance(x_user_id, str) and x_user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security violation: x-user-id header does not match verified JWT identity"
        )


    target_user_id = str(token_user_id)

    if not validate_uuid(target_user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user identity format: '{target_user_id}' is not a valid UUID"
        )

    return CurrentUser(user_id=target_user_id, email=email)



