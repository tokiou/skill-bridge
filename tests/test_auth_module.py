import unittest
from types import SimpleNamespace
import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import Response


def import_module_or_skip(test_case: unittest.TestCase, module_name: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        test_case.skipTest(f"Missing dependency for {module_name}: {exc}")


class AuthDependenciesTests(unittest.TestCase):
    def test_get_auth_service_injects_oauth_account_repository(self) -> None:
        dependencies = import_module_or_skip(self, "app.modules.auth.dependencies")

        user_repository = SimpleNamespace()
        oauth_account_repository = SimpleNamespace()
        token_service = SimpleNamespace()
        providers = {"google": SimpleNamespace()}
        uow = SimpleNamespace()

        auth_service = dependencies.get_auth_service(
            user_repository=user_repository,
            oauth_account_repository=oauth_account_repository,
            token_service=token_service,
            providers=providers,
            uow=uow,
        )

        self.assertIs(auth_service.user_repository, user_repository)
        self.assertIs(auth_service.oauth_account_repository, oauth_account_repository)
        self.assertIs(auth_service.token_service, token_service)
        self.assertIs(auth_service.providers, providers)
        self.assertIs(auth_service.uow, uow)


class AuthViewsTests(unittest.IsolatedAsyncioTestCase):
    def test_login_route_path_is_provider_segment(self) -> None:
        views = import_module_or_skip(self, "app.modules.auth.views")
        route_paths = {route.path for route in views.auth_router.routes}
        self.assertIn("/auth/{provider}", route_paths)

    async def test_callback_deletes_oauth_state_cookie_on_success(self) -> None:
        views = import_module_or_skip(self, "app.modules.auth.views")
        schemas = import_module_or_skip(self, "app.modules.auth.schemas")

        class FakeAuthService:
            async def authenticate_oauth_callback(self, **kwargs):
                return schemas.AuthTokens(access_token="token")

        response = Response()
        tokens = await views.oauth_callback(
            provider="google",
            auth_service=FakeAuthService(),
            response=response,
            code="code",
            state="state",
            expected_state="state",
        )

        self.assertEqual(tokens.access_token, "token")
        self.assertIn("oauth_state=\"\"", response.headers.get("set-cookie", ""))

    async def test_callback_raises_invalid_state_error(self) -> None:
        views = import_module_or_skip(self, "app.modules.auth.views")
        exceptions = import_module_or_skip(self, "app.modules.auth.exceptions")

        class FakeAuthService:
            async def authenticate_oauth_callback(self, **kwargs):
                raise exceptions.InvalidOAuthStateError("invalid state")

        with self.assertRaises(exceptions.InvalidOAuthStateError):
            await views.oauth_callback(
                provider="google",
                auth_service=FakeAuthService(),
                response=Response(),
                code="code",
                state="state",
                expected_state="other",
            )

    async def test_callback_raises_provider_error(self) -> None:
        views = import_module_or_skip(self, "app.modules.auth.views")
        exceptions = import_module_or_skip(self, "app.modules.auth.exceptions")

        class FakeAuthService:
            async def authenticate_oauth_callback(self, **kwargs):
                raise exceptions.UnsupportedAuthProviderError("unsupported")

        with self.assertRaises(exceptions.UnsupportedAuthProviderError):
            await views.oauth_callback(
                provider="invalid",
                auth_service=FakeAuthService(),
                response=Response(),
                code="code",
                state="state",
                expected_state="state",
            )

    async def test_callback_raises_external_identity_error(self) -> None:
        views = import_module_or_skip(self, "app.modules.auth.views")
        exceptions = import_module_or_skip(self, "app.modules.auth.exceptions")

        class FakeAuthService:
            async def authenticate_oauth_callback(self, **kwargs):
                raise exceptions.InvalidExternalIdentityError("invalid identity")

        with self.assertRaises(exceptions.InvalidExternalIdentityError):
            await views.oauth_callback(
                provider="google",
                auth_service=FakeAuthService(),
                response=Response(),
                code="code",
                state="state",
                expected_state="state",
            )

    async def test_callback_raises_unauthorized_error(self) -> None:
        views = import_module_or_skip(self, "app.modules.auth.views")
        exceptions = import_module_or_skip(self, "app.modules.auth.exceptions")

        class FakeAuthService:
            async def authenticate_oauth_callback(self, **kwargs):
                raise exceptions.UnauthorizedError("unauthorized")

        with self.assertRaises(exceptions.UnauthorizedError):
            await views.oauth_callback(
                provider="google",
                auth_service=FakeAuthService(),
                response=Response(),
                code="code",
                state="state",
                expected_state="state",
            )


class AuthExceptionHandlersTests(unittest.TestCase):
    def test_main_exception_handlers_map_status_codes(self) -> None:
        main_module = import_module_or_skip(self, "app.entrypoints.api.main")
        exceptions = import_module_or_skip(self, "app.modules.auth.exceptions")

        app = FastAPI()
        app.add_exception_handler(
            exceptions.InvalidOAuthStateError,
            main_module.handle_invalid_oauth_state,
        )
        app.add_exception_handler(
            exceptions.UnsupportedAuthProviderError,
            main_module.handle_unsupported_provider,
        )
        app.add_exception_handler(
            exceptions.InvalidExternalIdentityError,
            main_module.handle_invalid_external_identity,
        )
        app.add_exception_handler(
            exceptions.UnauthorizedError,
            main_module.handle_unauthorized,
        )
        app.add_exception_handler(
            exceptions.OAuthLinkConflictError,
            main_module.handle_oauth_link_conflict,
        )
        app.add_exception_handler(
            exceptions.OAuthPersistenceError,
            main_module.handle_oauth_persistence_error,
        )

        @app.get("/state")
        async def invalid_state_route():
            raise exceptions.InvalidOAuthStateError("invalid")

        @app.get("/provider")
        async def invalid_provider_route():
            raise exceptions.UnsupportedAuthProviderError("unsupported")

        @app.get("/identity")
        async def invalid_identity_route():
            raise exceptions.InvalidExternalIdentityError("identity")

        @app.get("/unauthorized")
        async def unauthorized_route():
            raise exceptions.UnauthorizedError("unauthorized")

        @app.get("/conflict")
        async def conflict_route():
            raise exceptions.OAuthLinkConflictError("conflict")

        @app.get("/persistence")
        async def persistence_route():
            raise exceptions.OAuthPersistenceError("persistence")

        client = TestClient(app)
        self.assertEqual(client.get("/state").status_code, 400)
        self.assertEqual(client.get("/provider").status_code, 400)
        self.assertEqual(client.get("/identity").status_code, 401)
        self.assertEqual(client.get("/unauthorized").status_code, 401)
        self.assertEqual(client.get("/conflict").status_code, 409)
        self.assertEqual(client.get("/persistence").status_code, 503)


if __name__ == "__main__":
    unittest.main()
