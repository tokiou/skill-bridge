from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.exceptions import (
    InvalidExternalIdentityError,
    InvalidOAuthStateError,
    OAuthLinkConflictError,
    OAuthPersistenceError,
    UnauthorizedError,
    UnsupportedAuthProviderError,
)
from app.modules.auth.views import auth_router


app = FastAPI()

api_router = APIRouter(prefix="/api")



def main_router(app: FastAPI):
    api_router.include_router(auth_router)
    app.include_router(api_router)


@app.exception_handler(InvalidOAuthStateError)
async def handle_invalid_oauth_state(
    request: Request,
    exc: InvalidOAuthStateError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(UnsupportedAuthProviderError)
async def handle_unsupported_provider(
    request: Request,
    exc: UnsupportedAuthProviderError,
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidExternalIdentityError)
async def handle_invalid_external_identity(
    request: Request,
    exc: InvalidExternalIdentityError,
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedError)
async def handle_unauthorized(
    request: Request,
    exc: UnauthorizedError,
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(OAuthLinkConflictError)
async def handle_oauth_link_conflict(
    request: Request,
    exc: OAuthLinkConflictError,
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(OAuthPersistenceError)
async def handle_oauth_persistence_error(
    request: Request,
    exc: OAuthPersistenceError,
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})



main_router(app)
