"""API v1 router — aggregates all v1 route modules with prefix /api/v1."""

from fastapi import APIRouter

from app.api.v1 import auth, exercises, sets, users, workouts

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
api_router.include_router(sets.router, tags=["sets"])
