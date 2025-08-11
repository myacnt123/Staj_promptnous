# my_fastapi_angular_backend_v2/app/api/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.Rooters.admin import is_user_admin_check
from app.database import crud
from app.database.models import PromptLike
from app.schemas import user as user_schemas
from app.core.security import verify_password, get_password_hash # For password verification/hashing
from app.api.deps import get_current_active_user
from app.database.database import get_db
from app.api.audit_deps import audit_request
router = APIRouter(
    prefix="/users",
    tags=["Users"], # New tag for OpenAPI/Swagger UI
)

# --- Endpoint 1: Get a list of all users (Admin-like functionality) ---
# This endpoint typically requires higher privileges (e.g., admin role).
# For now, it just requires any authenticated active user.

# --- Endpoint 2: Delete a user (Self-delete or Admin-delete) ---
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(audit_request)])
async def delete_user_endpoint(
    delete_user : user_schemas.UserDelete,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user account.
    A user can delete their own account. An administrator could delete any account.
    """
    if not(current_user.id == 1):
        if not(delete_user.current_password or verify_password(delete_user.current_password, current_user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Girilen mevcut parola hatalı",
                headers={"WWW-Authenticate": "Bearer"},
            )
    db_user = crud.get_user(db, user_id=delete_user.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")

    # Authorization check: User can only delete their own account for now
    if db_user.id != current_user.id or delete_user.user_id == 1 :
        # If you had an admin role, you'd check:
        # if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu kullanıcı hesabını silmek için yetkili değilsiniz")

    success = crud.delete_user(db, user_id=delete_user.user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kullanıcı silindi")
    return {"mesaj": "Kullanıcı hesabı silindi"}

# --- Endpoint 3: Change User Password (Authenticated user) ---
@router.put("/me/password", response_model=user_schemas.UserResponse)
async def change_password_endpoint(
    password_update: user_schemas.UserUpdatePassword,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Allows an authenticated user to change their password.
    Requires current password for verification.
    """
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Girilen mevcut parola hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Hash the new password
    hashed_new_password = get_password_hash(password_update.new_password)

    # Update password in DB
    updated_user = crud.update_user_password(db, user_id=current_user.id, hashed_new_password=hashed_new_password)

    if not updated_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Parola güncelleme başarısız")

    return updated_user

