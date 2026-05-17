import logging

from sqlalchemy.exc import IntegrityError

from app.modules.auth.exceptions import (
    InvalidExternalIdentityError,
    InvalidOAuthStateError,
    OAuthLinkConflictError,
    OAuthPersistenceError,
    UnauthorizedError,
    UnsupportedAuthProviderError,
)
from app.modules.auth.providers.base import OAuthProvider
from app.modules.auth.schemas import AuthTokens, ExternalIdentity
from app.modules.auth.services.token import TokenService
from app.modules.users.models import User
from app.modules.users.ports import OAuthAccountRepositoryPort, UserRepositoryPort
from app.shared.db.uow import UnitOfWork

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        *,
        user_repository: UserRepositoryPort,
        oauth_account_repository: OAuthAccountRepositoryPort,
        token_service: TokenService,
        providers: dict[str, OAuthProvider],
        uow: UnitOfWork,
    ) -> None:
        self.user_repository = user_repository
        self.oauth_account_repository = oauth_account_repository
        self.token_service = token_service
        self.providers = providers
        self.uow = uow

    def build_login_url(self, *, provider_name: str, state: str) -> str:
        provider = self._get_provider(provider_name)
        logger.info("oauth_login_url_built", extra={"provider": provider_name})
        return provider.build_login_url(state=state)

    async def authenticate_oauth_callback(
        self,
        *,
        provider_name: str,
        code: str,
        received_state: str,
        expected_state: str,
    ) -> AuthTokens:
        self._validate_state(received_state=received_state, expected_state=expected_state)
        provider = self._get_provider(provider_name)

        try:
            identity = await provider.exchange_code_for_identity(code=code)
            self._validate_identity(identity)
            user = await self._resolve_user(identity)
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            raise

        logger.info(
            "oauth_callback_authenticated",
            extra={"provider": identity.provider, "user_id": user.id},
        )
        return self.token_service.create_access_token(user_id=user.id)

    async def get_current_user(self, *, access_token: str) -> User:
        payload = self.token_service.decode_access_token(access_token)
        subject = payload.get("sub")
        if not subject:
            raise UnauthorizedError("Missing token subject")

        try:
            user_id = int(subject)
        except ValueError as exc:
            raise UnauthorizedError("Invalid token subject") from exc

        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        if not user.is_active:
            raise UnauthorizedError("Inactive user")
        return user

    async def _resolve_user(self, identity: ExternalIdentity) -> User:
        linked_user = await self.oauth_account_repository.get_user_by_provider_identity(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        )
        if linked_user is not None:
            user = await self.user_repository.update_profile(
                user=linked_user,
                email=identity.email,
                name=identity.name,
                avatar_url=identity.avatar_url,
            )
            await self.oauth_account_repository.update_from_identity(user=user, identity=identity)
            return user

        existing_user = await self.user_repository.get_by_email(identity.email)
        if existing_user is not None:
            await self._link_identity_with_retry(user=existing_user, identity=identity)
            return existing_user

        return await self._create_user_and_link_with_retry(identity)

    async def _create_user_and_link_with_retry(self, identity: ExternalIdentity) -> User:
        try:
            user = await self.user_repository.create(
                email=identity.email,
                name=identity.name,
                avatar_url=identity.avatar_url,
            )
            await self.oauth_account_repository.create_for_user(user=user, identity=identity)
            return user
        except IntegrityError:
            logger.warning(
                "oauth_create_race_detected",
                extra={"provider": identity.provider, "provider_user_id": identity.provider_user_id},
            )
            return await self._recover_from_race(identity)

    async def _link_identity_with_retry(self, *, user: User, identity: ExternalIdentity) -> None:
        try:
            await self.oauth_account_repository.create_for_user(user=user, identity=identity)
        except IntegrityError:
            winner = await self.oauth_account_repository.get_user_by_provider_identity(
                provider=identity.provider,
                provider_user_id=identity.provider_user_id,
            )
            if winner is None:
                raise OAuthPersistenceError("OAuth account link failed")
            if winner.id != user.id:
                raise OAuthLinkConflictError("OAuth identity already linked to another user")

    async def _recover_from_race(self, identity: ExternalIdentity) -> User:
        linked_user = await self.oauth_account_repository.get_user_by_provider_identity(
            provider=identity.provider,
            provider_user_id=identity.provider_user_id,
        )
        if linked_user is not None:
            return linked_user

        existing_user = await self.user_repository.get_by_email(identity.email)
        if existing_user is None:
            raise OAuthPersistenceError("Unable to recover OAuth persistence race")

        await self._link_identity_with_retry(user=existing_user, identity=identity)
        return existing_user

    def _get_provider(self, provider_name: str) -> OAuthProvider:
        provider = self.providers.get(provider_name)
        if provider is None:
            raise UnsupportedAuthProviderError("Unsupported auth provider")
        return provider

    def _validate_state(self, *, received_state: str, expected_state: str) -> None:
        if not expected_state:
            raise InvalidOAuthStateError("Missing OAuth state")
        if received_state != expected_state:
            raise InvalidOAuthStateError("Invalid OAuth state")

    def _validate_identity(self, identity: ExternalIdentity) -> None:
        if not identity.email:
            raise InvalidExternalIdentityError("External identity missing email")
        if not identity.email_verified:
            raise InvalidExternalIdentityError("External email is not verified")
        if not identity.provider_user_id:
            raise InvalidExternalIdentityError("External identity missing provider user id")
