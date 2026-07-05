from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from typing import Optional

from app.config import SUPABASE_URL, SUPABASE_AUTH_KEY, USE_SUPABASE_AUTH

# Security helper that auto-extracts 'Authorization: Bearer <token>'
# auto_error=False ensures we don't automatically fail with 403/401 when the header is missing,
# since in local-dev mode (without Supabase) the header is optional.
security = HTTPBearer(auto_error=False)

# Initialize Supabase auth client only when auth is configured.
supabase_client: Client = None
if USE_SUPABASE_AUTH:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_AUTH_KEY)
    except Exception as e:
        print(f"[AUTH ERROR] Failed to initialize Supabase auth client: {e}")

def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """
    Dependency that validates the user's Supabase JWT token if auth is active.
    Returns the user's UUID (str) if authenticated.
    If Supabase auth is NOT active (local-dev mode), returns None without raising errors.
    """
    if supabase_client is not None:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials are required."
            )
        token = credentials.credentials
        try:
            # Validate token against Supabase Auth server
            user_response = supabase_client.auth.get_user(token)
            user = user_response.user
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account no longer exists."
                )
            return user.id
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired credentials."
            )
    
    return None

