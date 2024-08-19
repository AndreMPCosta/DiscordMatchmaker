from fastapi import APIRouter

from api.consts import version

api_router = APIRouter(prefix=f"/api/{version}")
