from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.Rooters.admin import is_user_admin_check
from app.api.deps import get_current_admin_user, get_current_active_userv1, get_current_active_user
from app.database import crud  # Your CRUD functions
from app.database.database import get_db  # Your database session dependency
from app.database.models import User, Prompt
# Your label schemas
from app.schemas import label as label_schemas
from app.schemas.prompt import PromptWithLikeStatus
from app.schemas.user import UserInDB

# Assuming you have an authentication dependency, e.g., for admin users
# from app.dependencies import get_current_active_admin_user # Or similar

router = APIRouter(
    prefix="/labels",
    tags=["Labels"]
)


@router.post("/", response_model=label_schemas.LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_new_label(
        label: label_schemas.LabelCreate,
        db: Session = Depends(get_db),
        current_admin: UserInDB = Depends(get_current_admin_user),
        # You might want to protect this endpoint, e.g., only for admin users:
        # current_user: models.User = Depends(get_current_active_admin_user)
):
    """
    Create a new label.
    """
    db_label = crud.get_label_by_name(db, name=label.name)
    if db_label:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu isimde bir etiket hali hazırda bulunuyor"
        )

    return crud.create_label(db=db, label=label)

@router.delete("/{label_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label_endpoint(
    label_name: str = Path(..., min_length=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a label from the database. This is a permanent action.
    Requires admin privileges.
    """
    # Check for admin permissions
    if not (is_user_admin_check(db,current_user.id) or current_user.id==1): # Replace with your admin check
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can delete labels")

    if not crud.delete_label_by_name(db, label_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Label '{label_name}' not found")

    return None # Return HTTP 204 No Content


@router.put("/{label_id}", response_model=label_schemas.LabelResponse)
async def update_label_endpoint(
    label_update: label_schemas.LabelUpdate,
    label_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_active_userv1),
    db: Session = Depends(get_db)
):
    """
    Update a label's name. Requires admin privileges.
    """
    # Check for admin permissions
    if not (is_user_admin_check(db,current_user.id)or current_user.id==1): # Replace with your admin check function
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can update labels")

    updated_label = crud.update_label(db, label_id, label_update)
    if updated_label is None:
        # We need to distinguish between not found and name conflict
        existing_label_with_new_name = crud.get_label_by_name(db, label_update.name)
        if existing_label_with_new_name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A label with this name already exists")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Label with ID {label_id} not found")

    return updated_label




@router.get("/{label_name}", response_model=label_schemas.LabelResponse)
async def read_label(label_name: str, db: Session = Depends(get_db)):
    """
    Retrieve a label by its ID.
    """
    db_label = crud.get_label_by_name(db, name=label_name)
    if db_label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etiket bulunamadı")
    return db_label


@router.get("/", response_model=List[label_schemas.LabelResponse])
async def read_labels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of labels.
    """
    labels = crud.get_labels(db, skip=skip, limit=limit)
    return labels



@router.post("/{prompt_id}/labels/{label_name}", status_code=status.HTTP_201_CREATED)
async def add_label_to_prompt_endpoint(
    prompt_id: int,
    label_name: str ,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Adds a label to a prompt.
    Only the writer or an admin can add a label.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if db_prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    # Check for writer or admin permissions
    if db_prompt.user_id != current_user.id and not (is_user_admin_check(db,current_user.id) or current_user.id == 1):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this prompt")

    db_association = crud.add_label_to_prompt(db, prompt_id, label_name)
    if db_association is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Label is already associated with this prompt")

    return {"message": "Label added to prompt successfully"}


@router.delete("/{prompt_id}/labels/{label_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_label_from_prompt_endpoint(
    prompt_id: int,
    label_name: str ,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Removes a label from a prompt.
    Only the writer or an admin can remove a label.
    """
    db_prompt = crud.get_prompt(db, prompt_id=prompt_id)
    if db_prompt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    # Check for writer or admin permissions
    if db_prompt.user_id != current_user.id and not (is_user_admin_check(db,current_user.id) or current_user.id == 1):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this prompt")

    if not crud.remove_label_from_prompt(db, prompt_id, label_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label association not found for this prompt")

    return None # Return HTTP 204 No Content





# --- New Endpoints for Filtered Prompts ---

@router.get("/most-liked-by-label/{label_name}", response_model=List[PromptWithLikeStatus])
async def get_most_liked_prompts_by_label_endpoint(
    label_name: str ,
    db: Session = Depends(get_db),
    current_user: Optional[UserInDB] = Depends(get_current_active_userv1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve the most liked public prompts with a specific label,
    including whether the current authenticated user has liked them.
    """
    results = crud.get_most_liked_prompts_by_label_name_with_like_status(
        db,
        label_name,
        current_user,
        skip=skip,
        limit=limit
    )

    response_prompts = []
    if results is None:
        return []
    for item in results:
        if current_user:
            db_prompt_orm, is_liked_by_user = item
        else:
            db_prompt_orm = item
            is_liked_by_user = False

        prompt_with_status = PromptWithLikeStatus.from_orm(db_prompt_orm)
        prompt_with_status.is_liked_by_user = is_liked_by_user
        prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None
        response_prompts.append(prompt_with_status)

    return response_prompts


@router.get("/most-recent-by-label/{label_name}", response_model=List[PromptWithLikeStatus])
async def get_most_recent_prompts_by_label_endpoint(
    label_name: str ,
    db: Session = Depends(get_db),
    current_user: Optional[UserInDB] = Depends(get_current_active_userv1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Retrieve the most recent public prompts with a specific label,
    including whether the current authenticated user has liked them.
    """
    results = crud.get_most_recent_prompts_by_label_name_with_like_status(
        db,
        label_name,
        current_user,
        skip=skip,
        limit=limit
    )

    response_prompts = []
    if results is None:
        return []
    for item in results:
        if current_user:
            db_prompt_orm, is_liked_by_user = item
        else:
            db_prompt_orm = item
            is_liked_by_user = False

        prompt_with_status = PromptWithLikeStatus.from_orm(db_prompt_orm)
        prompt_with_status.is_liked_by_user = is_liked_by_user
        prompt_with_status.author_username = db_prompt_orm.author.username if db_prompt_orm.author else None
        response_prompts.append(prompt_with_status)

    return response_prompts


@router.get("/{prompt_id}/labels", response_model=List[label_schemas.LabelResponse])
async def get_labels_for_prompt_endpoint(
        prompt_id: int,
        db: Session = Depends(get_db),
        current_user: Optional[UserInDB] = Depends(get_current_active_userv1)
):
    """
    Retrieve labels for a specific prompt.
    Visible only if the prompt is public or the user is the author/admin.
    """
    labels = crud.get_labels_for_prompt(db, prompt_id, current_user)

    if labels is None:
        # The CRUD function returned None, which means the prompt was not found.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    if not labels:
        # The CRUD function returned an empty list, which means permissions were not met.
        # This is a bit ambiguous, so we should re-fetch the prompt to give a more specific error.
        db_prompt_exists = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if db_prompt_exists and not db_prompt_exists.is_public and (
                not current_user or db_prompt_exists.user_id != current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Not authorized to view labels for this prompt")
        # If the list is empty for other reasons (e.g., prompt has no labels),
        # it will just return an empty list, which is the correct behavior.

    return labels