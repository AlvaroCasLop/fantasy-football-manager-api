from src.app.modules.leagues.router import router as leagues_router
from src.app.modules.leagues.service import league_service

__all__ = ["league_service", "leagues_router"]
