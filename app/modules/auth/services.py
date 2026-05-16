from app.shared.config.settings import Settings
from functools import lru_cache
from dotenv import load_dotenv


load_dotenv()


@lru_cache
def get_settings():
    return Settings()


class AuthService:
    pass


class OauthProvider:
    pass


class GoogleOauthProvider:
    pass


class GithubOauthProvider:
    pass


class TokenService:
    pass


class UserRepository:
    pass