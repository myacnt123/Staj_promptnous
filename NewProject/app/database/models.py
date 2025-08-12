# my_fastapi_angular_backend_v2/app/database/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func  # For database functions like 'now()'
from sqlalchemy.orm import relationship  # <-- This import is crucial for relationships
from sqlalchemy.types import Integer as SQLInteger

from app.database.database import Base  # Import the declarative base


class User(Base):
    """SQLAlchemy ORM model for the 'users' table in the database."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)  # Define max length for String
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Store the hashed password
    is_active = Column(Boolean, default=True)  # Whether the user account is active
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Automatically set on creation
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Automatically updated on change


    # --- THESE ARE THE CRUCIAL MISSING LINES ---
    # Relationship to Prompt model: a User can have multiple Prompts
    # 'prompts' is the attribute on the User model that will contain a list of Prompt objects.
    # 'back_populates="author"' means the Prompt model has an 'author' attribute
    # that points back to this User.
    # 'cascade="all, delete-orphan"' ensures prompts are deleted if the user is deleted.
    prompts = relationship("Prompt", back_populates="author", cascade="all, delete-orphan")

    # Relationship to PromptLike model: a User can like multiple Prompts
    # 'likes' will be the attribute on User containing a list of PromptLike objects.
    # 'back_populates="user"' means the PromptLike model has a 'user' attribute
    # that points back to this User.
    # 'cascade="all, delete-orphan"' ensures likes are deleted if the user is deleted.
    likes = relationship("PromptLike", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("PromptComment", back_populates="user", cascade="all, delete-orphan")
    admin_entry = relationship(
        "AdminUser",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )

class Prompt(Base):
    """SQLAlchemy ORM model for the 'prompts' table."""
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    llm_link = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # --- THIS LINE IS REMOVED as per your goal to delete this column ---
    # no_of_likes = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", back_populates="prompts")
    liked_by_users = relationship("PromptLike", back_populates="prompt", cascade="all, delete-orphan")
    # --- THIS LINE REMAINS EXACTLY AS YOU PROVIDED IT ---
    comments = relationship("PromptComment", back_populates="prompt", cascade="all, delete-orphan")
    labels = relationship("PromptLabel", back_populates="prompt", cascade="all, delete-orphan")

    # --- ADD THIS BLOCK: no_of_likes as a hybrid_property ---
    @hybrid_property
    def no_of_likes(self) -> int:
        """
        Getter for no_of_likes. When accessing prompt_instance.no_of_likes,
        this returns the count of related PromptLike objects in Python.
        """
        return len(self.liked_by_users)

    @no_of_likes.expression
    def no_of_likes(cls):
        """
        Expression for no_of_likes. When used in a database query (e.g., order_by, filter),
        this constructs a SQL subquery to count likes efficiently.
        """
        # Ensure PromptLike is accessible here (this handles forward references if PromptLike is below Prompt)

        return (
            select(func.count(PromptLike.id))
            .where(PromptLike.prompt_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        ).cast(SQLInteger)
# --- PromptLike Model ---
class PromptLike(Base):
    """SQLAlchemy ORM model for the 'prompt_likes' table."""
    __tablename__ = "prompt_likes"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to the Prompt table - links a like to a specific prompt
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False, index=True)
    # Foreign key to the User table - links a like to the user who liked it
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)


    # ORM relationships
    # 'prompt' is the attribute on PromptLike pointing to the Prompt object.
    # 'back_populates="liked_by_users"' tells SQLAlchemy this is the other side of the relationship on Prompt.
    prompt = relationship("Prompt", back_populates="liked_by_users")

    # 'user' is the attribute on PromptLike pointing to the User object.
    # 'back_populates="likes"' tells SQLAlchemy this is the other side of the relationship on User.
    user = relationship("User", back_populates="likes")

    # Unique constraint to prevent a user from liking the same prompt multiple times.
    __table_args__ = (UniqueConstraint('prompt_id', 'user_id', name='_user_prompt_uc'),)

class PromptComment(Base):
    """SQLAlchemy ORM model for the 'prompt_comments' table."""
    __tablename__ = "prompt_comments"
    comment_id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    prompt = relationship("Prompt", back_populates="comments")
    user = relationship("User", back_populates="comments")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Label(Base):
    __tablename__ = "labels"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False) # Example field for a Label

    # Relationship to PromptLabel
    prompts_associated = relationship("PromptLabel", back_populates="label", cascade="all, delete-orphan")

class PromptLabel(Base):
    __tablename__ = "prompt_labels"

    # Define both foreign key columns as primary_key=True
    # This automatically makes their combination a composite primary key
    prompt_id = Column(Integer, ForeignKey("prompts.id"), primary_key=True)
    label_id = Column(Integer, ForeignKey("labels.id"), primary_key=True)

    # Define relationships to access the linked Prompt and Label objects
    # 'back_populates' links back to the relationship defined in Prompt and Label models
    prompt = relationship("Prompt", back_populates="labels") # 'labels' will be the attribute on Prompt
    label = relationship("Label", back_populates="prompts_associated") # 'prompts_associated' will be the attribute on Label



class AdminUser(Base):
    __tablename__ = "admins" # The table name for administrators

    # This 'user_id' column serves as both the PRIMARY KEY for 'admins'
    # and a FOREIGN KEY referencing the 'id' column in the 'users' table.
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, index=True)

    # Relationship back to User.
    user = relationship("User", back_populates="admin_entry")


class AuditLog(Base):
    __tablename__ = "audit_logs" # Or "audit_log" if you prefer singular

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    endpoint = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False) # IPv6 can be up to 45 chars
    user_id = Column(Integer, ForeignKey("users.id",ondelete='SET NULL'), nullable=True) # Nullable for unauthenticated requests
    username = Column(String(255), nullable=True) # Store username directly for easier querying

    # Optional: Relationship back to User if you want to query via user object
    user = relationship("User", backref="audit_logs")

    # Optional: You might want more details, e.g., method (GET/POST), status code, response time
    # method = Column(String(10), nullable=True)
    # status_code = Column(Integer, nullable=True)
    # response_time_ms = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, endpoint='{self.endpoint}', user_id={self.user_id}, ip='{self.ip_address}')>"