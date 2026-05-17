from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Protocol

from app.modules.users.models import OAuthAccount, User


class OAuthIdentityData(Protocol):
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        name: str | None,
        avatar_url: str | None,
        timezone: str = "America/Argentina/Buenos_Aires",
    ) -> User:
        user = User(
            email=email.lower(),
            name=name,
            avatar_url=avatar_url,
            timezone=timezone,
        )

        self.db.add(user)
        await self.db.flush()

        return user

    async def update_profile(
        self,
        *,
        user: User,
        email: str,
        name: str | None,
        avatar_url: str | None,
    ) -> User:
        user.email = email.lower()
        user.name = name
        user.avatar_url = avatar_url

        await self.db.flush()

        return user


class OAuthAccountRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_provider_identity(
        self,
        *,
        provider: str,
        provider_user_id: str,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .join(OAuthAccount)
            .where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )

        return result.scalar_one_or_none()

    async def create_for_user(
        self,
        *,
        user: User,
        identity: OAuthIdentityData,
    ) -> OAuthAccount:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
            provider_email=identity.email.lower(),
            email_verified=identity.email_verified,
        )

        self.db.add(oauth_account)
        await self.db.flush()

        return oauth_account

    async def update_from_identity(
        self,
        *,
        user: User,
        identity: OAuthIdentityData,
    ) -> None:
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == user.id,
                OAuthAccount.provider == identity.provider,
                OAuthAccount.provider_user_id == identity.provider_user_id,
            )
        )

        oauth_account = result.scalar_one_or_none()

        if oauth_account is None:
            return

        oauth_account.provider_email = identity.email.lower()
        oauth_account.email_verified = identity.email_verified

        await self.db.flush()
