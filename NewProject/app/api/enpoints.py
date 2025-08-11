# my_fastapi_angular_backend/app/api/endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

# Import necessary modules from your app
from app.database.database import get_db
from app.database import crud # Your CRUD operations
from app.schemas.user import UserCreate, UserPublic, UserInDB # User schemas for input/output
from app.schemas.token import Token # Token schema for response (includes AccessToken)
from app.core.security import verify_password, create_access_token # Security functions
from app.core.config import settings # Your app settings
from app.api.deps import get_current_active_user # For protecting API routes
from app.api.audit_deps import audit_request
router = APIRouter()

# --- API Endpoints ---

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED, dependencies=[Depends(audit_request)])
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user in the system.
    Returns the public user data upon successful registration.
    """
    db_user_by_username = crud.get_user_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kullanıcı adı çoktan alındı")

    db_user_by_email = crud.get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-posta çoktan alındı")

    new_user = crud.create_user(db=db, user=user_in)
    return UserPublic.model_validate(new_user)


@router.post("/token", response_model=Token,dependencies=[Depends(audit_request)])
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), # Expects 'username' and 'password' as form data
        db: Session = Depends(get_db)
):
    """
    Authenticates a user and provides a JWT token upon successful login.
    """
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yanlış kullanıcı adı veya parola",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Calculate token expiration time
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Create the JWT token, using username as the 'sub' (subject)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # Return the token and its type
    return {"access_token": access_token, "token_type": "bearer"}

# --- Protected API endpoint to get current user info ---
# This endpoint requires a valid JWT token to access.
@router.get("/me", response_model=UserPublic)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Returns the current authenticated user's public information.
    Requires a valid JWT token to be sent in the 'Authorization: Bearer <token>' header.
    """
    return UserPublic.model_validate(current_user)