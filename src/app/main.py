from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.core.config import settings
from src.app.core.exceptions import setup_exception_handlers
from src.app.modules.health.router import router as health_router
from src.app.modules.leagues.router import router as leagues_router
from src.app.modules.matches.router import router as matches_router
from src.app.modules.players.router import router as players_router
from src.app.modules.reference_data.router import router as reference_router
from src.app.modules.teams.router import router as teams_router



def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="FastAPI Backend for Fantasy Football / Blood Bowl Manager, ready for Railway & Supabase",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS for decoupled frontend clients (Next.js, Vite, Vue, React, etc.)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register domain exception handlers
    setup_exception_handlers(app)

    # Health check endpoints
    app.include_router(health_router)
    app.include_router(health_router, prefix=settings.API_V1_PREFIX)

    # Business Domain routers
    app.include_router(teams_router, prefix=settings.API_V1_PREFIX)
    app.include_router(players_router, prefix=settings.API_V1_PREFIX)
    app.include_router(leagues_router, prefix=settings.API_V1_PREFIX)
    app.include_router(matches_router, prefix=settings.API_V1_PREFIX)
    app.include_router(reference_router, prefix=settings.API_V1_PREFIX)




    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
            "status": "running",
        }

    return app


app = create_app()
