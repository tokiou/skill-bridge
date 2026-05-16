from fastapi import APIRouter, Request, Depends
from app.shared.config.settings import Settings
from functools import lru_cache
from dotenv import load_dotenv
from app.modules.auth.utils import oauth, create_access_token
from datetime import timedelta
from typing import Annotated


auth_router = APIRouter(prefix="/auth")
load_dotenv()


@lru_cache
def get_settings():
    return Settings()


@auth_router.get("/auth/google")
async def auth_google(request: Request, settings: Annotated[Settings, Depends(get_settings)]):
    return await oauth.google.authorize_redirect(request, redirect_uri=settings.REDIRECT_URI)


@auth_router.get("/auth/google/callback")
async def google_callback(request: Request,settings: Annotated[Settings, Depends(get_settings)]):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo") or {}

        username = user_info.get("email")

        access_token = create_access_token(
            settings, 
            data={"sub": username}, 
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            auth_method="google"
        )

        return {"access_token": access_token, "token": token}
    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        return {"error": str(e)}