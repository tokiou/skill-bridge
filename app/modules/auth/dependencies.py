from app.modules.auth.services import AuthService, TokenService
from app.modules.auth.providers.base import OAuthProvider
from app.modules.auth.providers.google import GoogleOauthProvider
from app.modules.users.repository import UserRepository, OAuthAccountRepository
from typing import Annotated
from fastapi import Depends
from app.shared.config.settings import Settings, get_settings
from app.shared.db.session import get_db
from app.shared.db.uow import SqlAlchemyUnitOfWork, UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


def get_user_repository(db: DbDep) -> UserRepository:
    return UserRepository(db=db)


def get_token_service(settings: SettingsDep) -> TokenService:
    return TokenService(settings=settings)


def get_google_oauth_provider(settings: SettingsDep) -> GoogleOauthProvider:
    return GoogleOauthProvider(settings=settings)


def get_uow(db: DbDep) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(db=db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
GoogleOauthProviderDep = Annotated[GoogleOauthProvider, Depends(get_google_oauth_provider)]
UowDep = Annotated[UnitOfWork, Depends(get_uow)]


def get_providers(
    google_provider: GoogleOauthProviderDep,
) -> dict[str, OAuthProvider]:
    return {
        "google": google_provider,
    }


ProvidersDep = Annotated[dict[str, OAuthProvider], Depends(get_providers)]


def get_oauth_account_repository(db: DbDep) -> OAuthAccountRepository:
    return OAuthAccountRepository(db=db)


OAuthAccountRepositoryDep = Annotated[
    OAuthAccountRepository,
    Depends(get_oauth_account_repository),
]


def get_auth_service(
        user_repository: UserRepositoryDep,
        oauth_account_repository: OAuthAccountRepositoryDep,
        token_service: TokenServiceDep,
        providers: ProvidersDep,
        uow: UowDep,
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        oauth_account_repository=oauth_account_repository,
        token_service=token_service,
        providers=providers,
        uow=uow,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]




 
