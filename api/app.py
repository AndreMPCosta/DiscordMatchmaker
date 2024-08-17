from contextlib import asynccontextmanager
from logging import getLogger
from os import environ, getenv

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from uvicorn import run as uvicorn_run

from api.db import get_db
from api.routers import api_router
from api.settings import get_secrets

secrets = get_secrets()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_beanie(
        database=get_db(),
        document_models=[],
        allow_index_dropping=False,
    )
    yield


app = FastAPI(
    title="Discord Matchmaker bot",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"operationsSorter": "method", "tagsSorter": "alpha"},
    default_response_class=ORJSONResponse,
)

origins = getenv("origins").split(",") if getenv("origins") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    # Log the problematic payload
    _logger = getLogger("Unprocessable Entity")
    _logger.error(f"detail: {exc.errors()}")
    return ORJSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    if exc.status_code == 400:
        # Log the problematic payload
        _logger = getLogger("Bad Request")
        _logger.error(f"detail: {exc.detail}")
        return ORJSONResponse(
            status_code=400,
            content={"detail": exc.detail},
        )
    # If it's not a 400 error, use the default HTTPException handler
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle exceptions that were not predicted on the code to avoid response headers missing
    """
    origin = request.headers.get("Origin")
    if origin in origins:
        allow_origin = origin
    else:
        allow_origin = "null"  # Or choose to handle this differently
    return ORJSONResponse(
        content={"detail": f"Internal Server Error - {type(exc).__name__}: {str(exc)}"},
        status_code=500,
        headers={
            "Access-Control-Allow-Origin": allow_origin,  # Allow the origin domain after being filtered
            "Access-Control-Allow-Methods": "*",  # Specify allowed methods
            "Access-Control-Allow-Headers": "*",  # Allow all headers
            "Access-Control-Allow-Credentials": "true",
        },
    )


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn_run(
        "api.app:app",
        host="0.0.0.0",
        port=int(environ.get("PORT", 16000)),
        log_level="info",
        workers=int(environ.get("WORKERS", 1)),
        ssl_certfile=secrets.cert_file_path if not environ.get("IS_LOCAL", False) else None,
        ssl_keyfile=secrets.key_file_path if not environ.get("IS_LOCAL", False) else None,
    )
