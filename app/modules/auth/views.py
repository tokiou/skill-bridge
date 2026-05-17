from fastapi import APIRouter, Response, Query, Cookie
import secrets
from app.modules.auth.dependencies import AuthServiceDep


auth_router = APIRouter(prefix="/auth")


@auth_router.get("/{provider}")
async def auth_login(
    auth_service: AuthServiceDep,
    provider: str,
    response: Response
):
    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=300,
    ) 
    login_url = auth_service.build_login_url(
        provider_name=provider,
        state=state,
    )

    return {
        "login_url": login_url
    }


@auth_router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    auth_service: AuthServiceDep,
    response: Response,
    code: str = Query(...),
    state: str = Query(...),
    expected_state: str | None = Cookie(default=None, alias="oauth_state"),
):
    tokens = await auth_service.authenticate_oauth_callback(
        provider_name=provider,
        code=code,
        received_state=state,
        expected_state=expected_state or "",
    )

    response.delete_cookie(key="oauth_state")

    return tokens
