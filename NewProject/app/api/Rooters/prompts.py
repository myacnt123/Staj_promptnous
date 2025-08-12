# my_fastapi_angular_backend_v2/app/api/routers/prompts.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import ValidationError
from sqlalchemy import Boolean, and_, desc
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Tuple

from sqlalchemy.sql.functions import current_user

from app.database import crud
from app.database.crud import get_prompts_count_by_label_name, get_prompts_count_by_label_name_auth, \
get_likes_count_for_user
from app.database.models import PromptLike, Prompt
from app.schemas import prompt as prompt_schemas
from app.schemas import user as user_schemas

# --- IMPORTANT: Import get_db and get_current_active_user directly ---
from app.api.deps import get_current_active_user, OptionalAuthUser, get_current_active_userv1, \
    get_current_user  # For authenticated user
from app.database.database import get_db # For DB session (the original generator)
from app.api.deps import get_current_admin_user
from app.api.audit_deps import audit_request
from app.database.models import Prompt as PromptModel
router = APIRouter(
    prefix="/prompts",
    tags=["Prompts"],
    # dependencies=[Depends(get_current_active_user)] # Only uncomment if ALL routes require auth
)

# --- REMOVED THE get_db_session() WRAPPER ---
# FastAPI's Depends() works directly with get_db() from app.database.database

# --- Endpoint 1: Create a new Prompt ---
@router.post("/", response_model=prompt_schemas.PromptPublic, status_code=status.HTTP_201_CREATED,dependencies=[Depends(audit_request)])
async def create_prompt_endpoint( # Changed to async def
    prompt: prompt_schemas.PromptCreate,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Logs are stored via dependencies = Depends(audit_request) parameter.
    Create a new prompt for the authenticated user.
    The user can specify if it's public or private.
    """
    db_prompt = crud.create_prompt(db=db, prompt=prompt, user_id=current_user.id)
    db_prompt.author_username = current_user.username
    return db_prompt


# --- Endpoint 2: Get a specific Prompt by ID ---
@router.get("/{prompt_id}", response_model=prompt_schemas.PromptPublic)

async def get_prompt_by_id_endpoint(
prompt_id: int,
db: Session = Depends(get_db), # Using get_db directly
current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_user)):
 db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
 if not db_prompt:
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
 if not db_prompt.is_public and (not current_user or db_prompt.user_id != current_user.id)and (current_user.id !=1):
  raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu promptu görmek için yetkili değilsiniz")
 db_prompt.author_username = db_prompt.author.username if db_prompt.author else None
 return db_prompt

@router.get("/{prompt_id/pure}", response_model=prompt_schemas.PromptPure)
async def get_prompt_by_id_pure_prompt( # Changed to async def
    prompt_id: int,
    db: Session = Depends(get_db), # Using get_db directly
    current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_user)
):
    """
    Retrieve a prompt by its ID.
    If the prompt is private, only the author can view it.
    Only accessible by the super administrator id = 1.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    # Check if prompt is private and user is not the author
    if not db_prompt.is_public and (not current_user or db_prompt.user_id != current_user.id) and (current_user.id !=1) :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu yorumu görmek için yetkili değilsiniz")
    db_return = crud.get_prompt_pure(db, prompt_id=prompt_id)

    return db_return

# --- Endpoint 3: Get prompts created by the current user ---
@router.get("/me/", response_model=List[prompt_schemas.PromptPublic])
async def get_my_prompts_endpoint( # Changed to async def
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db), # Using get_db directly
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all prompts created by the authenticated user.
    """
    prompts = crud.get_own_prompts(db, user_id=current_user.id, skip=skip, limit=limit)
    for prompt in prompts:
        prompt.author_username = current_user.username
    return prompts
@router.get("/user/{user_id}", response_model=List[prompt_schemas.PromptPublic]) # <-- CRUCIAL CHANGE HERE: added "/user"
async def get_user_prompts_endpoint(
    user_id: int,
    db: Session = Depends(get_db), # No current_user dependency here, making it truly public
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve all public prompts created by a specific user ID.
    This endpoint does NOT require authentication.
    """
    prompts = crud.get_prompts_by_user(db, user_id=user_id, skip=skip, limit=limit)

    for prompt in prompts:
        if prompt.author:
            prompt.author_username = prompt.author.username
        else:
            prompt.author_username = None
    return prompts


# --- Endpoint 4: Get all public prompts (most recent) ---
@router.get("/", response_model=List[prompt_schemas.PromptPublic])
async def get_all_public_prompts_endpoint( # Changed to async def
    db: Session = Depends(get_db), # Using get_db directly
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve the most recent public prompts with pagination.
    """
    prompts = crud.get_recent_public_prompts(db, skip=skip, limit=limit)
    for prompt in prompts:
        if prompt.author:
            prompt.author_username = prompt.author.username
    return prompts

# --- Endpoint 5: Get most liked public prompts ---
@router.get("/most-liked/", response_model=List[prompt_schemas.PromptPublic])
async def get_most_liked_public_prompts_endpoint( # Changed to async def
    db: Session = Depends(get_db), # Using get_db directly
    skip: int = 0,
    limit: int = 10
):
    """
    Retrieve the most liked public prompts with pagination.
    """
    prompts = crud.get_most_liked_public_prompts(db, skip=skip, limit=limit)
    for prompt in prompts:
        if prompt.author:
            prompt.author_username = prompt.author.username
    return prompts


# --- Endpoint 6: Get prompts liked by the current user (Favorites) ---
@router.get("/favorites/", response_model=List[prompt_schemas.PromptPublic])
async def get_my_liked_prompts_endpoint( # Changed to async def
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db), # Using get_db directly
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all prompts liked by the authenticated user.
    """
    prompts = crud.get_user_liked_prompts(db, user_id=current_user.id, skip=skip, limit=limit)
    for prompt in prompts:
        if prompt.author:
            prompt.author_username = prompt.author.username
    return prompts


# --- Endpoint 7: Update a Prompt ---
@router.put("/{prompt_id}", response_model=prompt_schemas.PromptPublic,dependencies=[Depends(audit_request)])
async def update_prompt_endpoint( # Changed to async def
    prompt_id: int,
    prompt_update: prompt_schemas.PromptCreate,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Update an existing prompt. Only the author can update their prompt.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    if db_prompt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu yorumu görmek için yetkili değilsiniz")

    updated_prompt = crud.update_prompt(db=db, prompt_id=prompt_id, prompt_update=prompt_update)
    if updated_prompt.author:
        updated_prompt.author_username = updated_prompt.author.username
    return updated_prompt


# --- Endpoint 8: Delete a Prompt ---
@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(audit_request)])
async def delete_prompt_endpoint( # Changed to async def
    prompt_id: int,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Delete a prompt. Only the author or super_admin can delete their prompt.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    if db_prompt.user_id != current_user.id and current_user.id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu promptu silmek için yetkili değilsiniz")

    crud.delete_prompt(db, prompt_id=prompt_id)
    return {"message": "Prompt başarılı bir şekilde silindi"}


# --- Endpoint 9: Like a Prompt ---
@router.post("/{prompt_id}/like", response_model=prompt_schemas.PromptLikePublic)
async def like_prompt_endpoint( # Changed to async def
    prompt_id: int,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Allow an authenticated user to like a prompt.
    Prevents liking own prompt or liking multiple times.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    # if db_prompt.user_id == current_user.id:
    #   raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like your own prompt")

    existing_like = crud.get_prompt_like(db, prompt_id=prompt_id, user_id=current_user.id)
    if existing_like:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prompt kullanıcı tarafından çoktan beğenildi")

    db_like = crud.create_prompt_like(db=db, prompt_id=prompt_id, user_id=current_user.id)
    return db_like



@router.get("/{prompt_id}/iflike", response_model=bool)
async def if_liked_prompt_endpoint( # Changed to async def
    prompt_id: int,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Returns if user liked a prompt
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    # if db_prompt.user_id == current_user.id:
    #   raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like your own prompt")

    existing_like = crud.get_prompt_like(db, prompt_id=prompt_id, user_id=current_user.id)
    if existing_like:
        return True
    else:
        return False




# --- Endpoint 10: Unlike a Prompt ---
@router.delete("/{prompt_id}/unlike", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_prompt_endpoint( # Changed to async def
    prompt_id: int,
    current_user: user_schemas.UserInDB = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Using get_db directly
):
    """
    Allow an authenticated user to unlike a prompt.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    existing_like = crud.get_prompt_like(db, prompt_id=prompt_id, user_id=current_user.id)
    if not existing_like:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu promptu henüz beğenmediniz")

    crud.delete_prompt_like(db=db, prompt_id=prompt_id, user_id=current_user.id)
    return {"mesaj": "Prompt beğenilenlerden kaldırıldı"}


@router.get("/{prompt_id}/status", response_model=prompt_schemas.PromptWithLikeStatus)
async def get_prompt_with_like_status_by_id(
        prompt_id: int,
        db: Session = Depends(get_db),
        # Use get_current_user, and its return type should be Optional[UserInDB]
        current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_userv1)
):
    """
    Retrieve a prompt by its ID, including whether the current user has liked it.
    Accessible by authenticated and unauthenticated users (for public prompts).
    """
    base_query = db.query(Prompt).filter(Prompt.id == prompt_id)

    # Initialize is_liked_by_user to False
    is_liked_by_user = False

    if current_user:  # This check is still necessary because current_user can be None
        query = base_query.outerjoin(
            PromptLike,
            and_(PromptLike.prompt_id == Prompt.id, PromptLike.user_id == current_user.id)
        ).add_columns(PromptLike.id.isnot(None).label("user_liked"))
        result = query.first()

        if result:  # Check if prompt was found with like status
            db_prompt_orm, is_liked_by_user = result
        else:
            db_prompt_orm = None  # Prompt not found
    else:
        db_prompt_orm = base_query.first()  # No join if not authenticated
        # is_liked_by_user remains False

    if not db_prompt_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt bulunamadı")

    # Privacy Check Logic
    if not db_prompt_orm.is_public:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Gizli promptlara erişim için kullanıcı doğrulama gerekiyor")
        if current_user.id != db_prompt_orm.user_id and current_user.id != 1:  # Assuming user.id 1 is superadmin
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Bu gizli promptu görmek için yetkili değilsiniz")

    prompt_with_status = prompt_schemas.PromptWithLikeStatus.from_orm(db_prompt_orm)
    prompt_with_status.is_liked_by_user = is_liked_by_user
    prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None

    return prompt_with_status


@router.get("/user/{user_id}/status", response_model=List[prompt_schemas.PromptWithLikeStatus])
async def get_user_prompts_by_id_with_like_status(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_userv1),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve public prompts created by a specific user ID,
    including whether the current authenticated user has liked them.
    If the current user is the author or super admin, their private prompts are also included.
    """
    # ADDED .options(joinedload(Prompt.author)) here
    base_query = db.query(Prompt).filter(Prompt.user_id == user_id).options(joinedload(Prompt.author))

    if current_user and (current_user.id == user_id or current_user.id == 1):
        pass
    else:
        base_query = base_query.filter(Prompt.is_public == True)

    if current_user:
        query = base_query.outerjoin(
            PromptLike,
            and_(PromptLike.prompt_id == Prompt.id, PromptLike.user_id == current_user.id)
        ).add_columns(PromptLike.id.isnot(None).label("user_liked"))
    else:
        query = base_query

    results = query.offset(skip).limit(limit).all()

    response_prompts = []
    for item in results:
        if current_user:
            db_prompt_orm, is_liked_by_user = item
        else:
            db_prompt_orm = item
            is_liked_by_user = False

        prompt_with_status = prompt_schemas.PromptWithLikeStatus.from_orm(db_prompt_orm)
        prompt_with_status.is_liked_by_user = is_liked_by_user
        prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None
        response_prompts.append(prompt_with_status)

    return response_prompts

@router.get("/tired/", response_model=List[prompt_schemas.PromptWithLikeStatus])
async def get_own_prompts_by_id_with_like_status(
        current_user: user_schemas.UserInDB = Depends(get_current_active_user),
        db: Session = Depends(get_db),  # Using get_db directly
        skip: int = 0,
        limit: int = 100
):
    """
    Retrieve public prompts created by a specific user ID,
    including whether the current authenticated user has liked them.
    If the current user is the author or super admin, their private prompts are also included.
    """
    # ADDED .options(joinedload(Prompt.author)) here
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,)
    user_id = current_user.id
    base_query = db.query(Prompt).filter(Prompt.user_id == user_id).options(joinedload(Prompt.author))

    if current_user and (current_user.id == user_id or current_user.id == 1):
        pass
    else:
        base_query = base_query.filter(Prompt.is_public == True)

    if current_user:
        query = base_query.outerjoin(
            PromptLike,
            and_(PromptLike.prompt_id == Prompt.id, PromptLike.user_id == current_user.id)
        ).add_columns(PromptLike.id.isnot(None).label("user_liked"))
    else:
        query = base_query

    results = query.offset(skip).limit(limit).all()

    response_prompts = []
    for item in results:
        if current_user:
            db_prompt_orm, is_liked_by_user = item
        else:
            db_prompt_orm = item
            is_liked_by_user = False

        prompt_with_status = prompt_schemas.PromptWithLikeStatus.from_orm(db_prompt_orm)
        prompt_with_status.is_liked_by_user = is_liked_by_user
        prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None
        response_prompts.append(prompt_with_status)

    return response_prompts




@router.get("/mosst-liked/", response_model=List[prompt_schemas.PromptWithLikeStatus])
async def get_most_liked_public_prompts_with_like_status(
        current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_userv1),
        db: Session = Depends(get_db),
        # Optional authentication to see like status for the logged-in user
        skip: int = 0,
        limit: int = 5
):
    """
    Retrieve the most liked public prompts with pagination,
    including whether the current authenticated user has liked each.
    """
    base_query = db.query(Prompt).filter(Prompt.is_public == True).order_by(desc(Prompt.no_of_likes))

    # Conditionally add the join for like status if current_user is authenticated
    if current_user:
        query = base_query.outerjoin(
            PromptLike,
            and_(PromptLike.prompt_id == Prompt.id, PromptLike.user_id == current_user.id)
        ).add_columns(PromptLike.id.isnot(None).label("user_liked"))
    else:
        query = base_query  # No join if not authenticated

    results = query.offset(skip).limit(limit).all()

    response_prompts = []
    for item in results:
        if current_user:
            db_prompt_orm, is_liked_by_user = item
        else:
            db_prompt_orm = item
            is_liked_by_user = False

        prompt_with_status = prompt_schemas.PromptWithLikeStatus.from_orm(db_prompt_orm)
        prompt_with_status.is_liked_by_user = is_liked_by_user
        prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None
        response_prompts.append(prompt_with_status)

    return response_prompts


@router.get("/public_likestatus_most_recent/", response_model=List[prompt_schemas.PromptWithLikeStatus])
async def get_all_public_prompts_with_like_status_recent(  # Renamed for clarity, original was /public/with-status
        current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_userv1),
        db: Session = Depends(get_db),
        # Optional authentication to see like status for the logged-in user
        skip: int = 0,
        limit: int = 5
):
    """
    Retrieve the most recent public prompts with pagination,
    including whether the current authenticated user has liked each.
    """
    base_query = db.query(Prompt).filter(Prompt.is_public == True).order_by(desc(Prompt.created_at))

    # Conditionally add the join for like status if current_user is authenticated
    if current_user:
        query = base_query.outerjoin(
            PromptLike,
            and_(PromptLike.prompt_id == Prompt.id, PromptLike.user_id == current_user.id)
        ).add_columns(PromptLike.id.isnot(None).label("user_liked"))
    else:
        query = base_query  # No join if not authenticated

    results = query.offset(skip).limit(limit).all()

    response_prompts = []
    for item in results:
        if current_user:
            db_prompt_orm, is_liked_by_user = item
        else:
            db_prompt_orm = item
            is_liked_by_user = False

        prompt_with_status = prompt_schemas.PromptWithLikeStatus.from_orm(db_prompt_orm)
        prompt_with_status.is_liked_by_user = is_liked_by_user
        prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None
        response_prompts.append(prompt_with_status)

    return response_prompts



@router.get("/getcounts/", response_model=int)
def get_prompts_count(
        db: Session = Depends(get_db)
):
    """
    Retrieves all public prompts and all private prompts belonging to the authorized user.
    """
    prompts = db.query(PromptModel).filter(Prompt.is_public == True).count()
    return prompts


@router.get("/getcountsown/", response_model=int)
def get_own_prompts_count(
        current_user: user_schemas.UserInDB = Depends(get_current_active_user),
        db: Session = Depends(get_db),

):
    """
    Retrieves all public prompts and all private prompts belonging to the authorized user.
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, )

    user_id = current_user.id

    prompts = db.query(PromptModel).filter(Prompt.user_id == user_id).count()
    return prompts



@router.get("/getcountslabel/", response_model=int)
def get_prompts_count_label(
        label_name: str,
        current_user: Optional[user_schemas.UserInDB] = Depends(get_current_active_userv1),
        db: Session = Depends(get_db),
):
    if not current_user:
        return get_prompts_count_by_label_name(db,label_name)
    return get_prompts_count_by_label_name_auth(db,label_name,current_user.id)


@router.get("/getcountsliked/", response_model=int)
def get_prompts_myliked_count_label(
        db: Session = Depends(get_db),
        current_user: user_schemas.UserInDB = Depends(get_current_active_user),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, )
    user_id = current_user.id
    return get_likes_count_for_user(db, user_id)