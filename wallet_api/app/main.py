from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints import wallets

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(wallets.router)


@app.get("/")
async def root():
    "Root endpoint with basic info about the API"
    return {
        "message": "Welcome to Wallet API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs"
    }


@app.get("/health")
async def health_check():
    "Health check endpoint to verify API is running"
    return {"status": "healthy"}