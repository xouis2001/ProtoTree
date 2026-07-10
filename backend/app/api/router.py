from fastapi import APIRouter

from app.api import (
    admin,
    auth,
    avatar,
    comments,
    commercial_protocols,
    contributions,
    folders,
    pitfalls,
    protocols,
    public_resources,
    taxonomy,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(avatar.router)
api_router.include_router(contributions.router)
api_router.include_router(protocols.router)
api_router.include_router(taxonomy.router)
api_router.include_router(commercial_protocols.router)
api_router.include_router(public_resources.router)
api_router.include_router(folders.router)
api_router.include_router(pitfalls.router)
api_router.include_router(comments.router)
api_router.include_router(comments.me_router)
