from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS

from app.db.database import Base, engine

# Database models
from app.db.models.user import User
from app.db.models.ticket import Ticket
from app.db.models.ticket_comment import TicketComment
from app.db.models.ticket_activity import TicketActivity

# API routers
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.tickets import router as ticket_router
from app.api.routes.chat import router as chat_router
from app.api.routes.ai import router as ai_router
from app.api.routes.comments import router as comments_router
from app.api.routes.activity import router as activity_router
from app.api.routes.dashboard import router as dashboard_router


# Create database tables
Base.metadata.create_all(bind=engine)


# FastAPI application
app = FastAPI(
    title="SupportSakhi AI",
    description="AI-powered real-world support platform",
    version="1.0.0"
)


# -----------------------------------
# CORS Configuration
# -----------------------------------

origins = CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------
# Register API Routers
# -----------------------------------

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ticket_router)
app.include_router(chat_router)
app.include_router(ai_router)
app.include_router(comments_router)
app.include_router(activity_router)
app.include_router(dashboard_router)


# -----------------------------------
# Root API
# -----------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to SupportSakhi AI",
        "status": "running",
        "version": "1.0.0"
    }


# -----------------------------------
# Health Check API
# -----------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SupportSakhi AI"
    }