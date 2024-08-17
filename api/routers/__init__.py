from fastapi import APIRouter

from consts import version

api_router = APIRouter(prefix=f"/api/{version}")
