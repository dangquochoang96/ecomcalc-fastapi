from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, auth
from app.database import engine
from app.models import user
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Initialize FastAPI with JWT security scheme
app = FastAPI(
    title="FastAPI Application",
    description="A well-structured FastAPI application",
    version="1.0.0",
    swagger_ui_parameters={"docExpansion": "expanded"}
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.on_event("startup")
def startup_event():
    """Create database tables on startup"""
    from app.database import Base
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to FastAPI Application"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
