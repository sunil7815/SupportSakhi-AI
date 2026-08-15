from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.db.database import Base, engine

# ============================================================
# DATABASE MODELS
# ============================================================

from app.db.models.user import User
from app.db.models.ticket import Ticket
from app.db.models.ticket_comment import TicketComment
from app.db.models.ticket_activity import TicketActivity
from app.db.models.resolution_attempt import ResolutionAttempt
from app.db.models.resolution_proof import ResolutionProof
from app.db.models.knowledge_item import KnowledgeItem


# ============================================================
# API ROUTERS
# ============================================================

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.tickets import router as ticket_router
from app.api.routes.chat import router as chat_router
from app.api.routes.ai import router as ai_router
from app.api.routes.comments import router as comments_router
from app.api.routes.activity import router as activity_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.knowledge import router as knowledge_router


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SupportSakhi AI",
    description="AI-powered real-world support platform",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTER API ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ticket_router)
app.include_router(chat_router)
app.include_router(ai_router)
app.include_router(comments_router)
app.include_router(activity_router)
app.include_router(dashboard_router)
app.include_router(knowledge_router)


# ============================================================
# ROOT API
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to SupportSakhi AI",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK API
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SupportSakhi AI",
        "features": {
            "smart_memory": True,
            "proof_of_resolution": True,
            "multi_agent_verification": True,
            "knowledge_base": True,
        },
    }