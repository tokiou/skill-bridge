from urllib.parse import urlencode

import httpx
from google.auth.transport import requests
from google.oauth2 import id_token

from app.modules.auth.exceptions import InvalidExternalIdentityError
from app.modules.auth.schemas import ExternalIdentity
from app.shared.config.settings import Settings


class GoogleOauthProvider:
    provider_name = "google"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_login_url(self, state: str) -> str:
        query_params = {
            "client_id": self.settings.GOOGLE_CLIENT_ID,
            "redirect_uri": self.settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(query_params)}"

    async def exchange_code_for_identity(self, code: str) -> ExternalIdentity:
        token_data = await self._exchange_code_for_tokens(code)
        google_id_token = token_data.get("id_token")

        if not google_id_token:
            raise InvalidExternalIdentityError("Missing Google id_token")

        payload = id_token.verify_oauth2_token(
            google_id_token,
            requests.Request(),
            self.settings.GOOGLE_CLIENT_ID,
        )

        google_sub = payload.get("sub")
        email = payload.get("email")

        if not google_sub:
            raise InvalidExternalIdentityError("Missing Google subject")
        if not email:
            raise InvalidExternalIdentityError("Missing Google email")

        return ExternalIdentity(
            provider=self.provider_name,
            provider_user_id=str(google_sub),
            email=str(email).lower(),
            email_verified=bool(payload.get("email_verified", False)),
            name=payload.get("name"),
            avatar_url=payload.get("picture"),
        )

    async def _exchange_code_for_tokens(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.settings.GOOGLE_CLIENT_ID,
                    "client_secret": self.settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.settings.GOOGLE_REDIRECT_URI,
                },
            )

        if response.status_code != 200:
            raise InvalidExternalIdentityError("Unable to exchange Google OAuth code")

        return response.json()
