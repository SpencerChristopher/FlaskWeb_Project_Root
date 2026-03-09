"""
Auth service for user credential and profile operations.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from src.events import dispatch_event, user_deleted, user_role_changed, user_created
from src.exceptions import UnauthorizedException, ConflictException, ValidationError
from src.models.user import User
from src.repositories.interfaces import UserRepository, TokenRepository
from src.services.roles import build_claim_roles_for_role
from src.schemas.base import password_policy

if TYPE_CHECKING:
    from src.services.session_service import SessionService


class AuthService:
    """Application service for auth-related user workflows.

    This service coordinates identity management, authentication, and session
    lifecycle operations. It delegates persistence to repositories and
    signals state changes through events.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        mongo_token_repository: TokenRepository | None = None,
        session_service: SessionService | None = None,
    ):
        """Initialize the AuthService with required repositories and services.

        Args:
            user_repository: Repository for user persistence.
            token_repository: Primary (Redis) repository for token blocklisting.
            mongo_token_repository: Secondary (Mongo) repository for persistent revocation.
            session_service: Service for managing active sessions and refresh tokens.
        """
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._mongo_token_repository = mongo_token_repository
        self._session_service = session_service

    def _validate_password_strength(self, password: str) -> None:
        """Enforces the centralized password complexity policy.

        Args:
            password: The plaintext password to validate.

        Raises:
            ValidationError: If the password fails any complexity requirements.
        """
        test_results = password_policy.test(password)
        if test_results:
            error_messages = []
            if "length" in test_results:
                error_messages.append(
                    f"Password must be at least {password_policy.length} characters long."
                )
            if "uppercase" in test_results:
                error_messages.append(
                    f"Password must contain at least {password_policy.uppercase} uppercase letter(s)."    
                )
            if "numbers" in test_results:
                error_messages.append(
                    f"Password must contain at least {password_policy.numbers} digit(s)."
                )
            if "special" in test_results:
                error_messages.append(
                    f"Password must contain at least {password_policy.special} special character(s)."     
                )

            # Use loc format consistent with Pydantic for frontend compatibility
            details = [
                {"loc": ["password"], "msg": msg, "type": "value_error"}
                for msg in error_messages
            ]
            raise ValidationError(
                message="Password does not meet complexity requirements.",
                details=details,
            )

    def authenticate(self, username: str, password: str) -> User:
        """Verify user credentials and return the user if valid.

        Args:
            username: The unique username.
            password: The plaintext password.

        Returns:
            User: The authenticated user instance.

        Raises:
            UnauthorizedException: If credentials do not match.
        """
        user = self._user_repository.get_by_username(username)
        if not user or not user.check_password(password):
            raise UnauthorizedException("Invalid username or password")
        return user

    def register_user(
        self, *, username: str, email: str, password: str, role: str = "member"
    ) -> User:
        """Registers a new user in the system.

        Performs uniqueness checks, validates password strength, and persists
         the new user. Dispatches a `user_created` event upon success.

        Args:
            username: Desired unique username.
            email: Contact email address.
            password: Plaintext password.
            role: Initial role assignment (defaults to 'member').

        Returns:
            User: The newly created user instance.

        Raises:
            ConflictException: If the username is already taken.
            ValidationError: If password strength requirements are not met.
        """
        if self._user_repository.get_by_username(username):
            raise ConflictException(f"Username '{username}' is already taken.")

        self._validate_password_strength(password)

        # In a real system, we'd also check email uniqueness if mandated

        new_user = User(username=username, email=email, role=role, token_version=0)
        new_user.set_password(password)
        created_user = self._user_repository.save(new_user)

        # Stage 3: ID-based signaling
        dispatch_event(
            user_created,
            "auth_service",
            user_id=str(created_user.id),
            username=created_user.username,
            role=created_user.role,
        )
        return created_user

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their unique ID.

        Args:
            user_id: The string representation of the user's ID.

        Returns:
            Optional[User]: The User instance if found, else None.
        """
        return self._user_repository.get_by_id(user_id)

    def get_user_or_raise(self, user_id: str, message: str = "Invalid user") -> User:
        """Retrieve a user by ID or raise an exception if not found.

        Args:
            user_id: The string representation of the user's ID.
            message: Custom error message for the exception.

        Returns:
            User: The found User instance.

        Raises:
            UnauthorizedException: If the user does not exist.
        """
        user = self.get_user(user_id)
        if not user:
            raise UnauthorizedException(message)
        return user

    def build_token_claims(self, user: User) -> dict[str, Any]:
        """Build the claims to be included in the JWT.

        Includes role-based permissions, username, and token version to enable
        stateless authorization with live revocation support.

        Args:
            user: The user for whom to build claims.

        Returns:
            dict[str, Any]: A dictionary of claims for the JWT payload.
        """
        return {
            "roles": build_claim_roles_for_role(user.role),
            "un": user.username,
            "tv": user.token_version,
        }

    def change_password(
        self, *, user_id: str, current_password: str, new_password: str
    ) -> None:
        """Change a user's password and increment their token version.

        Args:
            user_id: ID of the user changing their password.
            current_password: The existing plaintext password for verification.
            new_password: The new plaintext password.

        Raises:
            UnauthorizedException: If the current password is incorrect.
            ValidationError: If the new password fails complexity checks.
        """
        user = self.get_user_or_raise(user_id)
        if not user.check_password(current_password):
            raise UnauthorizedException("Invalid current password")

        self._validate_password_strength(new_password)
        user.set_password(new_password)
        user.token_version = (user.token_version or 0) + 1
        self._user_repository.save(user)
        self._invalidate_cached_version(user_id)

    def change_role(self, *, user_id: str, role: str) -> User:
        """Update a user's role and increment their token version.

        Args:
            user_id: ID of the user whose role is changing.
            role: The new role name.

        Returns:
            User: The updated user instance.
        """
        user = self.get_user_or_raise(user_id)
        if user.role != role:
            user.role = role
            user.token_version = (user.token_version or 0) + 1
            self._user_repository.save(user)
            self._invalidate_cached_version(user_id)
            # Stage 3: ID-based signaling
            dispatch_event(
                user_role_changed, "auth_service", user_id=str(user.id), new_role=role
            )
        return user

    def record_active_refresh_token(
        self, *, user_id: str, jti: str, ttl_seconds: int
    ) -> None:
        """Persist a refresh token JTI as active for a specific user.

        Args:
            user_id: The owner of the refresh token.
            jti: Unique identifier of the refresh token.
            ttl_seconds: Time-to-live for the token record.
        """
        if not self._session_service:
            return
        self._session_service.set_active_refresh_token(
            user_id=user_id,
            jti=jti,
            ttl_seconds=ttl_seconds,
        )

    def invalidate_session(self, user_id: str) -> None:
        """Invalidate all active sessions for a specific user.

        Args:
            user_id: The ID of the user whose sessions should be cleared.
        """
        if not self._session_service:
            return
        self._session_service.invalidate_session(user_id)

    def is_refresh_token_valid(self, user_id: str, jti: str) -> bool:
        """Check if a specific refresh token is still valid and active.

        Args:
            user_id: The claimed owner of the token.
            jti: The unique identifier of the token.

        Returns:
            bool: True if the token is active, False otherwise.
        """
        if not self._session_service:
            return True
        return self._session_service.is_refresh_token_valid(user_id, jti)

    def _invalidate_cached_version(self, user_id: str) -> None:
        """Clear the cached token version for a user in Redis.

        Args:
            user_id: The user ID to evict from cache.
        """
        if self._session_service:
            try:
                self._session_service._redis.delete(f"uver:{user_id}")
            except Exception:
                pass

    def delete_user(self, *, user_id: str) -> None:
        """Permanently delete a user and dispatch a removal event.

        Args:
            user_id: The ID of the user to delete.

        Raises:
            UnauthorizedException: If the user ID is invalid.
        """
        user = self.get_user_or_raise(user_id)
        persisted_user_id = str(user.id)
        self._user_repository.delete(user)
        # Stage 3: ID-based signaling
        dispatch_event(user_deleted, "auth_service", user_id=persisted_user_id)

    def revoke_token(self, jti: str, expires_at: datetime.datetime) -> None:
        """Revoke a token by adding its JTI to the blocklist.

        Args:
            jti: The unique identifier of the JWT.
            expires_at: The timestamp when the token would have expired.
        """
        self._token_repository.add_to_blocklist(jti, expires_at)
        # Also store in Mongo for long-term persistence/recovery
        if self._mongo_token_repository:
            try:
                self._mongo_token_repository.add_to_blocklist(jti, expires_at)
            except Exception:
                pass

    def is_token_revoked(self, jwt_payload: dict) -> bool:
        """Comprehensive check for token revocation.

        Checks Redis blocklist, falling back to MongoDB if Redis is unavailable.
        Also validates the token's version against the user's current version
        to handle mass-invalidation (e.g., password change).

        Args:
            jwt_payload: The decoded JWT payload.

        Returns:
            bool: True if the token should be rejected, False if it is valid.
        """
        jti = jwt_payload.get("jti")
        user_id = jwt_payload.get("sub")
        token_version = jwt_payload.get("tv")

        if not jti:
            return True

        # 1. Redis Check
        from src.exceptions import DatabaseConnectionException

        try:
            if self._token_repository.is_jti_revoked(jti):
                return True
        except DatabaseConnectionException:
            # 2. Redis Down -> Mongo Fallback
            if (
                self._mongo_token_repository
                and self._mongo_token_repository.is_jti_revoked(jti)
            ):
                return True

        if not user_id:
            return True

        # 3. Version Cache Check
        cache_key = f"uver:{user_id}"
        cached_version = None
        if self._session_service:
            try:
                cached_version = self._session_service._redis.get(cache_key)
            except Exception:
                pass

        if cached_version is not None:
            # Redis returns bytes, convert to int
            if token_version is not None and int(cached_version) != token_version:
                return True
            return False

        # 4. Mongo Identity Check (Cache Miss)
        user = self._user_repository.get_by_id(user_id)
        if not user:
            return True

        # Update Cache (5 minute TTL)
        if self._session_service and user.token_version is not None:
            try:
                self._session_service._redis.setex(
                    cache_key, 300, str(user.token_version)
                )
            except Exception:
                pass

        # If user has a token version, it must match the token's version
        if token_version is not None and user.token_version != token_version:
            return True

        return False
