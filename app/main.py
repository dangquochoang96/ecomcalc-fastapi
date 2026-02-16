from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, categories, platform_fees, users

# Initialize FastAPI with JWT security scheme
app = FastAPI(
    title="FastAPI Application",
    description="A well-structured FastAPI application",
    version="1.0.0",
    swagger_ui_parameters={"docExpansion": "expanded"},
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
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(
    platform_fees.router, prefix="/api/platform-fees", tags=["platform-fees"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔹 Startup
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    yield
    # 🔹 Shutdown (nếu cần)
    print("App shutdown")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to FastAPI Application"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
