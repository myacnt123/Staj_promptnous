# my_fastapi_angular_backend/app/api/deps.py

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError # For handling JWT decoding errors

from app.database.database import get_db # Import get_db from your database file
from app.database.models import User, AdminUser  # Your SQLAlchemy User model
from app.schemas.user import UserInDB # Your Pydantic UserInDB schema
from app.schemas.token import TokenPayload # Our token payload schema
from app.core.config import settings # Your settings for SECRET_KEY, ALGORITHM
from app.core.security import decode_token # The decode_token function from security.py

# This defines the OAuth2 scheme for extracting tokens from requests.
# 'tokenUrl' is the path where clients will send their username/password to get a token.
# This URL should match the FastAPI login endpoint, which is /auth/token in our setup.
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Dependency to get the current authenticated user from a JWT
async def get_current_user(
    db: Session = Depends(get_db), # Get a database session
    token: str = Depends(oauth2_scheme) # Get the token from the request's Authorization header
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token using your security function
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception

        # Validate the token payload based on your TokenPayload schema
        token_data = TokenPayload(**payload)
        if token_data.sub is None: # 'sub' field should contain the username (string)
            raise credentials_exception

        # Look up user by username (token_data.sub) in the database
        user = db.query(User).filter(User.username == token_data.sub).first()
        if user is None: # User not found in database
            raise credentials_exception

        # Return the user using your Pydantic UserInDB schema (for internal use)
        return UserInDB.model_validate(user)

    except JWTError: # Catch specific JWT errors during decode
        raise credentials_exception
"""

# 1. MODIFY oauth2_scheme: Add auto_error=False
# This tells OAuth2PasswordBearer to return None if no token is found, instead of raising an error.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


async def get_current_user(
    db: Session = Depends(get_db),
    # 2. MODIFY token parameter: Make it Optional[str]
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[UserInDB]: # 3. MODIFY return type hint: Make it Optional[UserInDB]
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 4. Handle the case where no token was provided (because auto_error=False)
    if token is None:
        return None # No token means no current user

    try:
        # Decode the token using your security function
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception

        # Validate the token payload based on your TokenPayload schema
        token_data = TokenPayload(**payload)
        if token_data.sub is None: # 'sub' field should contain the username (string)
            raise credentials_exception

        # Look up user by username (token_data.sub) in the database
        user = db.query(User).filter(User.username == token_data.sub).first()
        if user is None: # User not found in database
            raise credentials_exception

        # Return the user using your Pydantic UserInDB schema (for internal use)
        # Assuming UserInDB.model_validate is the correct way to convert
        return UserInDB.model_validate(user)

    except JWTError: # Catch specific JWT errors during decode
        # This catch is for cases where a token *was* provided but is invalid
        raise credentials_exception

async def get_current_active_user(

current_user: UserInDB = Depends(get_current_user),

) -> Optional[UserInDB]:

 if current_user is None:

  raise HTTPException(
status_code=status.HTTP_401_UNAUTHORIZED,
detail="Not authenticated or invalid credentials",
headers={"WWW-Authenticate": "Bearer"},
)
 if not current_user.is_active:
  raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
 return current_user

# Dependency to get the current active user (e.g., not disabled)
async def get_current_active_userv1(current_user: Optional[UserInDB] = Depends(get_current_user)) -> UserInDB:
 if current_user is None:
    return None

# Now that we've confirmed current_user is NOT None, we can safely access its attributes
 if not current_user.is_active:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

 return current_user


async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_user), # First, ensure the user is authenticated
    db: Session = Depends(get_db)
) -> UserInDB:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    """
    Dependency that checks if the current authenticated user is an admin.
    """
    # Check if the current user's ID exists in the 'admins' table
    is_admin = db.query(AdminUser).filter(AdminUser.user_id == current_user.id).first()

    if (not is_admin) and current_user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Admin privileges required."
        )
    return current_user # Return the authenticated user object if they are an admin

async def OptionalAuthUser(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[UserInDB]:
    """
    Dependency to get the current user, but returns None if authentication fails or no token provided.
    Allows endpoints to be accessible by both authenticated and unauthenticated users.
    """
    if not token: # No token provided in Authorization header
        return None
    try:
        # Attempt to get the user using the standard get_current_user logic
        # If get_current_user is async, you MUST await it here!
        return await get_current_user(token, db) # <--- ADD 'await' HERE!
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise # Re-raise any other HTTPExceptions