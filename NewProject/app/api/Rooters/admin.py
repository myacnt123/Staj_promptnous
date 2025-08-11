from typing import List

from fastapi import APIRouter, Depends, HTTPException, status , Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user

from app.api.deps import get_current_admin_user, get_current_active_user
from app.core.security import get_password_hash
from app.database import crud
from app.database.crud import get_user_count
from app.schemas import user as user_schemas
from app.database.database import get_db
from app.schemas.user import UserPublic, UserInDB
from app.database.models import AdminUser, User as UserModel
from app.schemas import prompt as prompt_schemas
from app.api.audit_deps import audit_request

router = APIRouter(prefix="/admin", tags=["admin-management"])

def is_user_admin_check(db: Session, user_id: int) -> bool:
    """
    Checks if a given user ID corresponds to an administrator.
    This function can be called from any other function that has access to a DB session.
    """
    admin_entry = db.query(AdminUser).filter(AdminUser.user_id == user_id).first()
    return bool(admin_entry) # Returns True if found, False otherwise

@router.post("/add_admin/{user_id}", response_model=UserPublic, status_code=status.HTTP_201_CREATED,dependencies=[Depends(audit_request)])
async def add_user_to_admins(
    user_id: int,
    current_admin: UserInDB = Depends(get_current_admin_user), # This endpoint requires admin privileges
    db: Session = Depends(get_db)
):
    """
    Adds a user to the 'admins' table, granting them admin privileges.
    Accessible only by existing administrators.
    """
    # 1. Check if the target user exists in the main users table
    user_to_make_admin = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user_to_make_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")

    # 2. Check if they are already an admin
    existing_admin_entry = db.query(AdminUser).filter(AdminUser.user_id == user_id).first()
    if existing_admin_entry or user_id == 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kullanıcı zaten yönetici")

    # 3. Create a new AdminUser entry
    new_admin = AdminUser(user_id=user_id) # Assign the user_id to the PK/FK column
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin) # Refresh to get any default values/relationship updates

    return UserPublic.model_validate(user_to_make_admin) # Return public data of the now-admin user

@router.delete("/remove_admin/{user_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(audit_request)])
async def remove_user_from_admins(
    user_id: int,
    current_admin: UserInDB = Depends(get_current_admin_user), # This endpoint requires admin privileges
    db: Session = Depends(get_db)
):
    """
    Removes a user from the 'admins' table, revoking their admin privileges.
    Accessible only by existing administrators.
    """
    # Prevent an admin from removing themselves unless explicitly desired
    #if current_admin.id != 1:
    #    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not a root administrator.")
    if user_id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bir yönetici kendini yönetici listesinden çıkaramaz")

    # Find and delete the admin entry by its user_id
    admin_entry = db.query(AdminUser).filter(AdminUser.user_id == user_id).first()
    if not admin_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı yönetici statüsüne sahip değil")

    db.delete(admin_entry)
    db.commit()
    return {"message": "Kullanıcı yönetici listesinden başarıyla çıkartıldı"}

# You might want to list all admins (optional)
@router.get("/list_admins", response_model=list[UserPublic])
async def list_admins(
    current_admin: UserInDB = Depends(get_current_admin_user), # Requires admin
    db: Session = Depends(get_db)
):
    """
    Lists all users who currently have admin privileges.
    """
    admin_users = db.query(AdminUser).all()
    # Eagerly load user data for all admin entries to avoid N+1 problem if needed
    # You might consider joining with User model here if you frequently need user details for admins
    admin_user_ids = [admin_entry.user_id for admin_entry in admin_users]
    users_with_admin_priv = db.query(UserModel).filter(UserModel.id.in_(admin_user_ids)).all()
    return [UserPublic.model_validate(user) for user in users_with_admin_priv]

@router.get("/", response_model=List[user_schemas.UserResponse])
async def read_users(
    db: Session = Depends(get_db),
    current_admin: UserInDB = Depends(get_current_admin_user),  # Requires admin,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve a list of all users. Requires authentication.
    Note: In a real application, this would typically be restricted to administrators.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users



@router.put("/{prompt_id}/soft-delete", response_model=prompt_schemas.PromptPublic,dependencies=[Depends(audit_request)])
async def deleted_byadmin_prompt_endpoint( # Changed to async def
    prompt_id: int,
    current_admin: UserInDB = Depends(get_current_admin_user),  # Requires admin,
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Admin-level endpoint to soft-delete a prompt by marking its content.
    Only accessible by administrators.
    Admins CANNOT delete posts authored by other administrators.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    if  db_prompt.user_id == 1 : #is_user_admin_check(db,db_prompt.user_id) or
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this prompt")

    update_string = "Bu prompt admin tarafından silindi admin_id: " + str(current_admin.id)
    prompt_update = prompt_schemas.PromptCreate(content=update_string)
    updated_prompt = crud.update_prompt(db=db, prompt_id=prompt_id, prompt_update=prompt_update)
    if updated_prompt.author:
        updated_prompt.author_username = updated_prompt.author.username
    return updated_prompt



@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(audit_request)])
async def admin_delete_user_endpoint(
    user_id: int,
    current_admin: UserInDB = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user account.
    A user can delete their own account. An administrator could delete any account except for superadmin and other administrators.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")

    # Authorization check: User can only delete their own account for now
    if is_user_admin_check(db,user_id) or user_id == 1 : #is_user_admin_check(db,user_id) or
        # If you had an admin role, you'd check:
        # if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu kullanıcıyı silmek için gerekli yetkilere sahip değilsiniz")

    success = crud.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kullanıcı silindi")
    return {"mesaj": "Kullanıcı başarılı bir şekilde silindi"}

""""
# super_admin password update of users
@router.put("/{user_id}/password_change", response_model=user_schemas.UserResponse,dependencies=[Depends(audit_request)])
async def chanegd_byadmin_password_endpoint( # Changed to async def
    password_update: user_schemas.UserUpdatePassword,
    user_id: int,
    current_admin: UserInDB = Depends(get_current_admin_user),  # Requires admin,
    db: Session = Depends(get_db) # Using get_db directly
):

   # Admin-level endpoint to soft-delete a prompt by marking its content.
   # Only accessible by administrators.
   # Admins CANNOT delete posts authored by other administrators.

    db_user = crud.get_user(db, user_id=user_id)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_id == 1 or current_user.id != 1 :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update password")

    hashed_new_password = get_password_hash(password_update.new_password)
    updated_user = crud.update_user_password(db,user_id = user_id,hashed_new_password=hashed_new_password)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password update failed")
    return updated_user
 """
@router.get("/ifadmin/", response_model=bool)
async def if_admin( # Changed to async def
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if is_user_admin_check(db,current_user.id) or current_user.id == 1:
        return True
    else:
        return False

@router.get("/usercount/", response_model=int)
async def get_count_user(
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if is_user_admin_check(db, current_user.id) or current_user.id == 1:
        return get_user_count(db)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to get user count")
