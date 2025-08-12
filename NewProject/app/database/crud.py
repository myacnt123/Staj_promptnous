# my_fastapi_angular_backend/app/database/crud.py
from typing import Optional, List, Tuple

from fastapi.params import Depends

from app.database.database import get_db
from app.schemas import comment as comment_schemas

from sqlalchemy import and_, or_, distinct
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import desc, func ,select

from app.database import models
from app.database.models import User, Prompt  # Import your SQLAlchemy ORM model
from app.schemas.label import LabelUpdate
from app.schemas.user import UserCreate, UserUpdate  # Import your Pydantic schema for input
from app.core.security import get_password_hash # Import your hashing utility
from app.schemas import prompt as prompt_schemas
from app.schemas import user as user_schemas
from app.schemas import label as label_schemas


def create_prompt(db: Session, prompt: prompt_schemas.PromptCreate, user_id: int ):
    " Create a new prompt "
    db_prompt = models.Prompt(
        **prompt.model_dump(),
        user_id=user_id
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt
def get_prompt(db: Session, prompt_id: int ):
    " Get a prompt by prompt_id "
    return db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()


def get_prompt_pure(db: Session, prompt_id: int ):
    " Get a prompt by prompt_id but only content of it for llm connection "
    return db.query(models.Prompt.content).filter(models.Prompt.id == prompt_id).first()





def get_public_prompts(db: Session, skip: int = 0, limit: int = 100) -> List[models.Prompt]:
    """Retrieves all public prompts."""
    return db.query(models.Prompt).filter(models.Prompt.is_public == True).offset(skip).limit(limit).all()

def get_recent_public_prompts(db: Session, skip: int = 0, limit: int = 10) -> List[models.Prompt]:
    """Retrieves the most recent public prompts with pagination."""
    return db.query(models.Prompt)\
             .filter(models.Prompt.is_public == True)\
             .order_by(desc(models.Prompt.created_at))\
             .offset(skip).limit(limit).all()

def get_prompts_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Prompt]:
    """Retrieves all prompts belonging to a specific user."""
    return db.query(models.Prompt).options(joinedload(models.Prompt.author)).filter(models.Prompt.is_public == True,
                                                                                    models.Prompt.user_id == user_id).order_by(
        desc(models.Prompt.created_at)) \
        .offset(skip).limit(limit).all()

def get_own_prompts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Prompt]:
    """Retrieves all prompts belonging to current user."""
    return db.query(models.Prompt).options(joinedload(models.Prompt.author)).filter(
        models.Prompt.user_id == user_id).order_by(desc(models.Prompt.created_at)) \
        .offset(skip).limit(limit).all()


def create_prompt_like(db: Session, prompt_id: int, user_id: int):
    """Creates a new like for a prompt by a user."""
    existing_like = db.query(models.PromptLike).filter(
        and_(models.PromptLike.prompt_id == prompt_id, models.PromptLike.user_id == user_id)
    ).first()

    if existing_like:
        return existing_like  # Already liked, no new like needed

    db_like = models.PromptLike(prompt_id=prompt_id, user_id=user_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def delete_prompt_like(db: Session, prompt_id: int, user_id: int):
    """Deletes a like for a prompt by a user."""
    db_like = db.query(models.PromptLike).filter(
        and_(models.PromptLike.prompt_id == prompt_id, models.PromptLike.user_id == user_id)
    ).first()
    if db_like:
        db.delete(db_like)
        db.commit()
    return db_like


def get_prompt_like(db: Session, prompt_id: int, user_id: int):
    """Checks if a user has liked a specific prompt."""
    return db.query(models.PromptLike).filter(
        and_(models.PromptLike.prompt_id == prompt_id, models.PromptLike.user_id == user_id)
    ).first()

def get_user_liked_prompts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Prompt]:
    """Retrieves all prompts liked by a specific user."""
    return db.query(models.Prompt)\
             .join(models.PromptLike, models.Prompt.id == models.PromptLike.prompt_id)\
             .filter(models.PromptLike.user_id == user_id)\
             .offset(skip).limit(limit).all()


def get_most_liked_public_prompts(db: Session, skip: int = 0, limit: int = 10) -> List[models.Prompt]:
    """Retrieves the most liked public prompts directly using the no_of_likes column."""

    result = db.query(models.Prompt) \
        .filter(models.Prompt.is_public == True) \
        .order_by(desc(models.Prompt.no_of_likes)) \
        .offset(skip).limit(limit).all()

    return result



def update_prompt(db: Session, prompt_id: int, prompt_update: prompt_schemas.PromptCreate):
    """Updates an existing prompt (excluding no_of_likes, which is managed by like/unlike operations)."""
    db_prompt = db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()
    if db_prompt:
        # Exclude no_of_likes from regular updates
        update_data = prompt_update.model_dump(exclude_unset=True)
        update_data.pop('no_of_likes', None) # Ensure no_of_likes isn't updated via this method
        for key, value in update_data.items():
            setattr(db_prompt, key, value)
        db.commit()
        db.refresh(db_prompt)
    return db_prompt

def delete_prompt(db: Session, prompt_id: int):
    """Deletes a prompt by its ID."""
    db_prompt = db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()
    if db_prompt:
        db.delete(db_prompt)
        db.commit()
    return db_prompt




def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieves a user from the database by their username."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves a user from the database by their email address."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """
    Creates a new user in the database.
    Hashes the password before storing it.
    """
    # 1. Hash the plain-text password from the Pydantic UserCreate schema
    hashed_password = get_password_hash(user.password)

    # 2. Create an instance of the SQLAlchemy ORM User model
    db_user = User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True # Default to active upon creation
    )

    # 3. Add to session, commit, and refresh to get the database-generated ID (if any)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, user_id: int, user_update: user_schemas.UserUpdate):
    """Updates a user's profile information."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        # model_dump(exclude_unset=True) ensures only provided fields are updated
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.add(db_user) # Add to session (might be redundant if already in session, but safe)
        db.commit()
        db.refresh(db_user)
    return db_user # Returns the updated user object or None if not found


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Retrieves a list of users with pagination."""
    # Note: No joinedload for relationships here, consistent with your preference.
    # If User had relationships that needed to be eager-loaded for the UserResponse,
    # you would add options(joinedload(...)) here.
    return db.query(models.User).offset(skip).limit(limit).all()

# --- NEW: Function to delete a user ---
def delete_user(db: Session, user_id: int):
    """Deletes a user by ID."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return True # Returns True if successfull deletion
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    return db_user

# --- NEW: Function to update a user's password ---
def update_user_password(db: Session, user_id: int, hashed_new_password: str):
    """Updates a user's hashed password."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.hashed_password = hashed_new_password
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user




def create_comment(
    db: Session,
    comment: comment_schemas.CommentCreate,
    user_id: int,
    prompt_id: int
) -> models.PromptComment:
    """Creates a new comment for a given prompt by a given user."""
    db_comment = models.PromptComment(
        prompt_id=prompt_id,
        user_id=user_id,
        content=comment.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comment(db: Session, comment_id: int) -> Optional[models.PromptComment]:
    """Retrieves a single comment by its ID."""
    return db.query(models.PromptComment).filter(models.PromptComment.comment_id == comment_id).first()


def get_comments_for_prompt(
    db: Session,
    prompt_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[models.PromptComment]:
    """Retrieves all comments for a specific prompt, ordered by creation date."""
    return db.query(models.PromptComment)\
        .filter(models.PromptComment.prompt_id == prompt_id)\
        .order_by(desc(models.PromptComment.created_at))\
        .offset(skip).limit(limit).all()

def update_comment(
    db: Session,
    comment_id: int,
    comment_update: comment_schemas.CommentUpdate # Use the update schema
) -> Optional[models.PromptComment]:
    """Updates the content of an existing comment."""
    db_comment = db.query(models.PromptComment).filter(models.PromptComment.comment_id == comment_id).first()
    if db_comment:
        # Assuming only content can be updated for comments based on CommentUpdate schema
        db_comment.content = comment_update.content
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
    return db_comment



def delete_comment(db: Session, comment_id: int):
    """Deletes a comment by its ID."""
    db_comment = db.query(models.PromptComment).filter(models.PromptComment.comment_id == comment_id).first()
    if db_comment:
        db.delete(db_comment)
        db.commit()
        return True # Indicate success
    return False # Comment not found or not deleted



def create_label(db: Session, label: label_schemas.LabelCreate) -> models.Label:
    """
    Creates a new label in the database.
    Checks for existing label with the same name to prevent duplicates.
    """
    db_label = models.Label(name=label.name)
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label

def delete_label_by_name(db: Session, label_name: str) -> bool:
    """
    Deletes a label from the database, safely without removing prompts.
    It first removes all associations to prompts and then deletes the label.
    Returns True if deleted, False if not found.
    """
    db_label = get_label_by_name(db, label_name)
    if db_label:
        # Step 1: Manually delete all associations for this label
        # This prevents the prompts themselves from being deleted
        db.query(models.PromptLabel).filter(models.PromptLabel.label_id == db_label.id).delete(synchronize_session=False)

        # Step 2: Now that the associations are gone, safely delete the label
        db.delete(db_label)
        db.commit()
        return True
    return False



def update_label(db: Session, label_id: int, label_update: LabelUpdate) -> models.Label | None:
    """
    Updates a label's name. Returns the updated label object, or None if the label
    does not exist or the new name is already taken.
    """
    db_label = db.query(models.Label).filter(models.Label.id == label_id).first()
    if not db_label:
        return None  # Label not found

    # Check if the new name is already taken by a different label
    existing_label = db.query(models.Label).filter(models.Label.name == label_update.name).first()
    if existing_label and existing_label.id != label_id:
        return None  # New name is already in use by another label

    db_label.name = label_update.name
    db.commit()
    db.refresh(db_label)
    return db_label


def get_label_by_name(db: Session, name: str) -> models.Label | None:
    """
    Retrieves a label by its name.
    """
    return db.query(models.Label).filter(models.Label.name == name).first()

def get_label(db: Session, label_id: int) -> models.Label | None:
    """
    Retrieves a label by its ID.
    """
    return db.query(models.Label).filter(models.Label.id == label_id).first()


def get_labels(db: Session, skip: int = 0, limit: int = 100) -> list[models.Label]:
    """
    Retrieves a list of labels with pagination.
    """
    return db.query(models.Label).offset(skip).limit(limit).all()


def add_label_to_prompt(db: Session, prompt_id: int, label_name: str) -> models.PromptLabel | None:
    """
    Creates a new PromptLabel association. Returns None if association already exists or label not found.
    """
    db_label = db.query(models.Label).filter(models.Label.name == label_name).first()
    if not db_label:
        return None  # Label name not found

    existing_association = db.query(models.PromptLabel).filter(
        and_(models.PromptLabel.prompt_id == prompt_id, models.PromptLabel.label_id == db_label.id)
    ).first()

    if existing_association:
        return None  # Association already exists

    db_association = models.PromptLabel(prompt_id=prompt_id, label_id=db_label.id)
    db.add(db_association)
    db.commit()
    db.refresh(db_association)
    return db_association


def remove_label_from_prompt(db: Session, prompt_id: int, label_name: str) -> bool:
    """
    Deletes a PromptLabel association. Returns True if deleted, False if not found.
    """
    db_label = db.query(models.Label).filter(models.Label.name == label_name).first()
    if not db_label:
        return False # Label name not found

    db_association = db.query(models.PromptLabel).filter(
        and_(models.PromptLabel.prompt_id == prompt_id, models.PromptLabel.label_id == db_label.id)
    ).first()

    if db_association:
        db.delete(db_association)
        db.commit()
        return True
    return False

# --- New CRUD Functions for Filtered Prompts ---
def get_most_liked_prompts_by_label_name_with_like_status(
    db: Session,
    label_name: str,
    current_user: user_schemas.UserInDB | None,
    skip: int = 0,
    limit: int = 10
) -> list[models.Prompt] | list[tuple[models.Prompt, bool]] | None:
    """
    Retrieves most liked public prompts with a specific label name, including like status for the user.
    Returns None if the label does not exist.
    """
    # First, find the label by its unique name
    db_label = db.query(models.Label).filter(models.Label.name == label_name).first()
    if not db_label:
        return None  # Return None if label name is not found

    base_query = db.query(models.Prompt).join(models.PromptLabel)\
        .filter(models.Prompt.is_public == True, models.PromptLabel.label_id == db_label.id)\
        .order_by(desc(models.Prompt.no_of_likes))

    if current_user:
        query = base_query.outerjoin(
            models.PromptLike,
            and_(models.PromptLike.prompt_id == models.Prompt.id, models.PromptLike.user_id == current_user.id)
        ).add_columns(models.PromptLike.id.isnot(None).label("user_liked"))
    else:
        query = base_query

    return query.offset(skip).limit(limit).all()


def get_most_recent_prompts_by_label_name_with_like_status(
    db: Session,
    label_name: str,
    current_user: user_schemas.UserInDB | None,
    skip: int = 0,
    limit: int = 10
) -> list[models.Prompt] | list[tuple[models.Prompt, bool]] | None:
    """
    Retrieves most recent public prompts with a specific label name, including like status for the user.
    Returns None if the label does not exist.
    """
    # First, find the label by its unique name
    db_label = db.query(models.Label).filter(models.Label.name == label_name).first()
    if not db_label:
        return None  # Return None if label name is not found

    base_query = db.query(models.Prompt).join(models.PromptLabel)\
        .filter(models.Prompt.is_public == True, models.PromptLabel.label_id == db_label.id)\
        .order_by(desc(models.Prompt.created_at))

    if current_user:
        query = base_query.outerjoin(
            models.PromptLike,
            and_(models.PromptLike.prompt_id == models.Prompt.id, models.PromptLike.user_id == current_user.id)
        ).add_columns(models.PromptLike.id.isnot(None).label("user_liked"))
    else:
        query = base_query

    return query.offset(skip).limit(limit).all()


def get_labels_for_prompt(
    db: Session,
    prompt_id: int,
    current_user: Optional[user_schemas.UserInDB]
) -> List[models.Label] | None:
    """
    Retrieves labels for a prompt, with a permission check.
    Returns a list of Label objects, or None if the prompt does not exist.
    """
    # Eagerly load the prompt and its labels in one query
    db_prompt = db.query(models.Prompt).options(
        joinedload(models.Prompt.labels).joinedload(models.PromptLabel.label)
    ).filter(models.Prompt.id == prompt_id).first()

    if db_prompt is None:
        return None # Prompt not found

    # Permission check:
    # 1. Is the prompt public?
    # 2. Is there a current user and are they the author of the prompt?
    # 3. Is there a current user and are they an admin?
    if (current_user):
     is_author = current_user and db_prompt.user_id == current_user.id
     is_admin = current_user.id == 1 # Your admin check function
    else:
     is_author = False
     is_admin = False

    if db_prompt.is_public or is_author or is_admin:
        # Extract the labels from the association objects
        labels = [pl.label for pl in db_prompt.labels]
        return labels
    else:
        # Not authorized, so return an empty list or raise an exception in the router
        return []

def get_prompts_count_by_label_name(db: Session, label_name: str) -> int:
    """
    Returns the count of prompts associated with a given label name.
    """
    return (db.query(models.Prompt).join(models.PromptLabel).join(models.Label).filter(
        models.Label.name == label_name,

    ).filter(
        or_(
            models.Prompt.is_public == True
        )
    ).count())

def get_prompts_count_by_label_name_auth(db: Session, label_name: str, user_id: int) -> int:
    """
    Returns the count of prompts associated with a given label name,
    where the prompts are either public or owned by the specified user.
    """
    return db.query(models.Prompt).join(models.PromptLabel).join(models.Label).filter(
        models.Label.name == label_name
    ).filter(
        or_(
            models.Prompt.is_public == True,
            models.Prompt.user_id == user_id,
            user_id ==1
        )
    ).count()


def get_likes_count_for_user(db: Session, user_id: int) -> int:
    """
    Returns the total number of likes a user has given.
    """
    return (db.query(models.PromptLike).join(models.Prompt).filter(
        models.PromptLike.user_id == user_id,
    ).filter(
        or_(
            models.Prompt.is_public == True,
            models.Prompt.user_id == user_id,
        )
    ).count())

def get_user_count(db: Session) -> int:
    return db.query(models.User).count()