import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, digest, papers, preferences, users
from app.core.config import settings

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT != "test":
        from app.tasks.scheduler import start_scheduler
        start_scheduler()
        logger.info("PaperNosh API started (environment=%s)", settings.ENVIRONMENT)
    yield
    if settings.ENVIRONMENT != "test":
        from app.tasks.scheduler import stop_scheduler
        stop_scheduler()


app = FastAPI(
    title="PaperNosh API",
    description="Personalized academic paper delivery platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://papernosh.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(preferences.router)
app.include_router(papers.router)
app.include_router(digest.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
