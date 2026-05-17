from app.shared.config.settings import Settings
from functools import lru_cache
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
import os


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