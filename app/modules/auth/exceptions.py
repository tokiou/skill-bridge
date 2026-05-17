class AuthError(Exception):
    """Base exception for auth module."""


class InvalidExternalIdentityError(AuthError):
    """Raised when external OAuth identity is invalid."""


class InvalidOAuthStateError(AuthError):
    """Raised when OAuth state is invalid or expired."""


class UnsupportedAuthProviderError(AuthError):
    """Raised when the OAuth provider is not supported."""


class UnauthorizedError(AuthError):
    """Raised when the user is not authorized."""


class OAuthLinkConflictError(AuthError):
    """Raised when an OAuth identity cannot be linked safely."""


class OAuthPersistenceError(AuthError):
    """Raised when OAuth persistence fails after retries."""
