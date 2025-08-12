# my_fastapi_angular_backend/app/schemas/token.py

from pydantic import BaseModel
from typing import Optional

class AccessToken(BaseModel):
    """Schema for the JWT access token returned upon successful login."""
    access_token: str
    token_type: str = "bearer" # Standard token type for JWTs

class Token(AccessToken):
    """
    Alias for AccessToken. Used as the response_model for the /token endpoint.
    This allows flexibility if you later want 'Token' to contain more fields
    than just the raw access token.
    """
    pass

class TokenPayload(BaseModel):
    """
    Schema for the data expected within the JWT payload.
    'sub' (subject) is a standard JWT claim, here used to store the username.
    """
    sub: Optional[str] = None # 'sub' will contain the username (a string)
    # You can add other standard JWT claims or custom claims here if needed, e.g.:
    # exp: Optional[int] = None # Expiration time (handled automatically by jose)
    # user_id: Optional[int] = None # If you wanted to include the user ID