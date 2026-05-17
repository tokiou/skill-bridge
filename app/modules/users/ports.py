from typing import Protocol

from app.modules.users.models import OAuthAccount, User


class OAuthIdentityData(Protocol):
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool


class UserRepositoryPort(Protocol):
    async def get_by_id(self, user_id: int) -> User | None:
        ...

    async def get_by_email(self, email: str) -> User | None:
        ...

    async def create(
        self,
        *,
        email: str,
        name: str | None,
        avatar_url: str | None,
        timezone: str = "America/Argentina/Buenos_Aires",
    ) -> User:
        ...

    async def update_profile(
        self,
        *,
        user: User,
        email: str,
        name: str | None,
        avatar_url: str | None,
    ) -> User:
        ...


class OAuthAccountRepositoryPort(Protocol):
    async def get_user_by_provider_identity(
        self,
        *,
        provider: str,
        provider_user_id: str,
    ) -> User | None:
        ...

    async def create_for_user(
        self,
        *,
        user: User,
        identity: OAuthIdentityData,
    ) -> OAuthAccount:
        ...

    async def update_from_identity(
        self,
        *,
        user: User,
        identity: OAuthIdentityData,
    ) -> None:
        ...
