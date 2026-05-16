from app.modules.auth.services import (GoogleOauthProvider,
                                       AuthService,
                                       GithubOauthProvider,
                                       TokenService,
                                       UserRepository,
                                       OauthProvider)
from typing import Annotated
from fastapi import Depends
from app.shared.config.settings import Settings, get_settings
from app.shared.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


def get_user_repository(db: DbDep) -> UserRepository:
    return UserRepository(db=db)


def get_token_service(settings: SettingsDep) -> TokenService:
    return TokenService(settings=settings)


def get_gh_oauth_provider(settings: SettingsDep) -> GithubOauthProvider:
    return GithubOauthProvider(settings=settings)


def get_google_oauth_provider(settings: SettingsDep) -> GoogleOauthProvider:
    return GoogleOauthProvider(settings=settings)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
GoogleOauthProviderDep = Annotated[GoogleOauthProvider, Depends(get_google_oauth_provider)]
GithubOauthProviderDep = Annotated[GithubOauthProvider, Depends(get_gh_oauth_provider)]


def get_providers(
    google_provider: GoogleOauthProviderDep,
    github_provider: GithubOauthProviderDep
) -> dict[str, OauthProvider]:
    return {
        "google": google_provider,
        "github": github_provider
    }


ProvidersDep = Annotated[dict[str, OauthProvider], Depends(get_providers)]


def get_auth_service(
        user_repository = UserRepositoryDep,
        token_service = TokenServiceDep,
        providers = ProvidersDep
) -> AuthService:
    return AuthService(
        auth_repository=user_repository,
        token_service=token_service,
        providers=providers,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]




 