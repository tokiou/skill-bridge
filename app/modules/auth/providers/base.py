from typing import Protocol

from app.modules.auth.schemas import ExternalIdentity


class OAuthProvider(Protocol):
    def build_login_url(self, state: str) -> str:
        ...

    async def exchange_code_for_identity(self, code: str) -> ExternalIdentity:
        ...
