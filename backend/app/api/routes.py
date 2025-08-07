from fastapi import APIRouter

from app.api.endpoints import clubs, fixtures, management, matches, players, seasons

api_router = APIRouter()

api_router.include_router(clubs.router, prefix="/clubs", tags=["clubs"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(seasons.router, prefix="/seasons", tags=["seasons"])
api_router.include_router(fixtures.router, prefix="/fixtures", tags=["fixtures"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(management.router, prefix="/management", tags=["management"])