from fastapi import APIRouter

from app.api.routes import auth, discovery, documents, ingestions, preferences, push, recommendations, search, tasks

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(ingestions.router, prefix="/ingestions", tags=["ingestions"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

api_router.include_router(push.router, prefix="/push", tags=["push"])
