# my_fastapi_angular_backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Important for Angular frontend

from app.api.Rooters import labels
# Import necessary database components for table creation
from app.database.database import Base, engine

# Import the authentication router from your endpoints file
from app.api.enpoints import router as auth_router
from app.api.Rooters.prompts import router as prompts_router
from app.api.Rooters.users import router as users_router
from app.api.Rooters.comment import router as comments_router
from app.api.Rooters.admin import router as admin_router

# --- Database Initialization ---
# This line attempts to create all tables defined by SQLAlchemy's Base.metadata.
# It's suitable for development as it ensures tables exist.
# In a production environment, you would typically use Alembic for migrations.
Base.metadata.create_all(bind=engine)

# --- FastAPI Application Setup ---
app = FastAPI(
    title="FastAPI Auth API Backend for Angular",
    description="A pure API backend for an Angular application, with user authentication and MySQL.",
    version="0.1.0",
)

# --- CORS Middleware ---
# This is CRUCIAL when your frontend (Angular) is served from a different origin
# (e.g., Angular on http://localhost:4200 and FastAPI on http://localhost:8000).
# You should restrict `allow_origins` to your Angular app's URL in production.
origins = [
    "http://localhost",
    "http://localhost:8080", # Example if your Angular app runs here
    "http://localhost:4200", # Common Angular development server port
    f"http://10.6.20.186:4200",
    # Add your Angular app's production URL here when deployed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers (including Authorization header for JWT)
)

# --- Include API Routers ---
# This includes the authentication-related endpoints from app/api/endpoints.py
# All routes defined in that router will be prefixed with "/auth"
# and tagged with "Authentication" in the OpenAPI (Swagger) documentation.
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(prompts_router ,tags=["Prompts"])
app.include_router(users_router , tags=["Users"])

app.include_router(admin_router )

app.include_router(comments_router)

app.include_router(labels.router)

# --- Root Endpoint ---
# For a pure API, the root often just returns a simple message.
@app.get("/")
async def read_root():
    """
    Root endpoint for the API, indicates successful server startup.
    Go to /docs for interactive API documentation (Swagger UI).
    """
    return {"message": "Welcome to the FastAPI Auth API! Check /docs for API documentation."}