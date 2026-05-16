from app.shared.config.settings import Settings
from functools import lru_cache
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta
import jwt


load_dotenv()


@lru_cache
def get_settings():
    return Settings()


oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ['GOOGLE_CLIENT_ID'],
    client_secret=os.environ['GOOGLE_CLIENT_SECRET'],
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"scope": "openid email profile"},
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
)


def create_access_token(settings, data: dict, expires_delta: timedelta | None = None, auth_method="password"):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire, "auth_method": auth_method})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt