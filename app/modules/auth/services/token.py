from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from app.modules.auth.exceptions import UnauthorizedError
from app.modules.auth.schemas import AuthTokens
from app.shared.config.settings import Settings


class TokenService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_access_token(self, *, user_id: int) -> AuthTokens:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "type": "access",
        }
        token = jwt.encode(
            payload,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM,
        )
        return AuthTokens(access_token=token)

    def decode_access_token(self, access_token: str) -> dict:
        try:
            payload = jwt.decode(
                access_token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM],
            )
        except InvalidTokenError as exc:
            raise UnauthorizedError("Invalid access token") from exc

        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")

        return payload
