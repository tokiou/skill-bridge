import unittest
from types import SimpleNamespace

from sqlalchemy.exc import IntegrityError

from app.modules.auth.exceptions import (
    InvalidExternalIdentityError,
    OAuthLinkConflictError,
)
from app.modules.auth.schemas import ExternalIdentity
from app.modules.auth.services.auth import AuthService


class AuthServiceBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def test_callback_rolls_back_on_error(self) -> None:
        identity = ExternalIdentity(
            provider="google",
            provider_user_id="pid-1",
            email="user@example.com",
            email_verified=False,
        )

        class FakeProvider:
            async def exchange_code_for_identity(self, code: str) -> ExternalIdentity:
                return identity

            def build_login_url(self, state: str) -> str:
                return "https://example.com"

        class FakeUow:
            def __init__(self) -> None:
                self.commits = 0
                self.rollbacks = 0

            async def commit(self) -> None:
                self.commits += 1

            async def rollback(self) -> None:
                self.rollbacks += 1

        uow = FakeUow()

        service = AuthService(
            user_repository=SimpleNamespace(),
            oauth_account_repository=SimpleNamespace(),
            token_service=SimpleNamespace(),
            providers={"google": FakeProvider()},
            uow=uow,
        )

        with self.assertRaises(InvalidExternalIdentityError):
            await service.authenticate_oauth_callback(
                provider_name="google",
                code="code",
                received_state="state",
                expected_state="state",
            )

        self.assertEqual(uow.commits, 0)
        self.assertEqual(uow.rollbacks, 1)

    async def test_identity_link_conflict_is_raised(self) -> None:
        identity = ExternalIdentity(
            provider="google",
            provider_user_id="pid-2",
            email="user@example.com",
            email_verified=True,
        )
        existing_user = SimpleNamespace(id=1)
        winner_user = SimpleNamespace(id=99)

        class FakeProvider:
            async def exchange_code_for_identity(self, code: str) -> ExternalIdentity:
                return identity

            def build_login_url(self, state: str) -> str:
                return "https://example.com"

        class FakeUserRepo:
            async def get_by_id(self, user_id: int):
                return None

            async def get_by_email(self, email: str):
                return existing_user

            async def create(self, **kwargs):
                return None

            async def update_profile(self, **kwargs):
                return None

        class FakeOAuthRepo:
            def __init__(self) -> None:
                self.calls = 0

            async def get_user_by_provider_identity(self, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    return None
                return winner_user

            async def create_for_user(self, **kwargs):
                raise IntegrityError("stmt", "params", Exception("dup"))

            async def update_from_identity(self, **kwargs):
                return None

        class FakeUow:
            async def commit(self) -> None:
                return None

            async def rollback(self) -> None:
                return None

        service = AuthService(
            user_repository=FakeUserRepo(),
            oauth_account_repository=FakeOAuthRepo(),
            token_service=SimpleNamespace(create_access_token=lambda user_id: None),
            providers={"google": FakeProvider()},
            uow=FakeUow(),
        )

        with self.assertRaises(OAuthLinkConflictError):
            await service.authenticate_oauth_callback(
                provider_name="google",
                code="code",
                received_state="state",
                expected_state="state",
            )
