from pydantic import BaseModel
from dataclasses import dataclass


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UsrInDB(User):
    hashed_password: str


@dataclass(frozen=True)
class ExternalIdentity:
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    name: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    token_type: str = "bearer"