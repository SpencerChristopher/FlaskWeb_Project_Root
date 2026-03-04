"""
Auth service for user credential and profile operations.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from src.events import dispatch_event, user_deleted, user_role_changed, user_created
from src.exceptions import UnauthorizedException, ConflictException
from src.models.user import User
from src.repositories.interfaces import UserRepository, TokenRepository
from src.services.roles import build_claim_roles_for_role

if TYPE_CHECKING:
    from src.services.session_service import SessionService


class AuthService:
    """Application service for auth-related user workflows."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        mongo_token_repository: TokenRepository | None = None,
        session_service: SessionService | None = None,
    ):
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._mongo_token_repository = mongo_token_repository
        self._session_service = session_service

    def authenticate(self, username: str, password: str) -> User:
        user = self._user_repository.get_by_username(username)
        if not user or not user.check_password(password):
            raise UnauthorizedException("Invalid username or password")
        return user

    def register_user(self, *, username: str, email: str, password: str, role: str = "member") -> User:
        """
        Registers a new user in the system.
        Only allowed for administrative users (enforced at route level).
        """
        if self._user_repository.get_by_username(username):
            raise ConflictException(f"Username '{username}' is already taken.")
        
        # In a real system, we'd also check email uniqueness if mandated
        
        new_user = User(
            username=username,
            email=email,
            role=role,
            token_version=0
        )
        new_user.set_password(password)
        created_user = self._user_repository.save(new_user)
        
        # Stage 3: ID-based signaling
        dispatch_event(
            user_created, 
            "auth_service", 
            user_id=str(created_user.id), 
            username=created_user.username,
            role=created_user.role
        )
        return created_user

    def get_user(self, user_id: str) -> Optional[User]:
        return self._user_repository.get_by_id(user_id)

    def get_user_or_raise(self, user_id: str, message: str = "Invalid user") -> User:
        user = self.get_user(user_id)
        if not user:
            raise UnauthorizedException(message)
        return user

    def build_token_claims(self, user: User) -> dict[str, Any]:
        """
        Build the claims to be included in the JWT.
        Includes minimal role, username, and version info to enable stateless 
        authorization with backend-derived permissions and display metadata.
        """
        return {
            "roles": build_claim_roles_for_role(user.role),
            "un": user.username,
            "tv": user.token_version,
        }

    def change_password(
        self, *, user_id: str, current_password: str, new_password: str
    ) -> None:
        user = self.get_user_or_raise(user_id)
        if not user.check_password(current_password):
            raise UnauthorizedException("Invalid current password")

        user.set_password(new_password)
        user.token_version = (user.token_version or 0) + 1
        self._user_repository.save(user)
        self._invalidate_cached_version(user_id)

    def change_role(self, *, user_id: str, role: str) -> User:
        user = self.get_user_or_raise(user_id)
        if user.role != role:
            user.role = role
            user.token_version = (user.token_version or 0) + 1
            self._user_repository.save(user)
            self._invalidate_cached_version(user_id)
            # Stage 3: ID-based signaling
            dispatch_event(user_role_changed, "auth_service", user_id=str(user.id), new_role=role)
        return user

    def record_active_refresh_token(self, *, user_id: str, jti: str, ttl_seconds: int) -> None:
        if not self._session_service:
            return
        self._session_service.set_active_refresh_token(
            user_id=user_id,
            jti=jti,
            ttl_seconds=ttl_seconds,
        )

    def invalidate_session(self, user_id: str) -> None:
        if not self._session_service:
            return
        self._session_service.invalidate_session(user_id)

    def is_refresh_token_valid(self, user_id: str, jti: str) -> bool:
        if not self._session_service:
            return True
        return self._session_service.is_refresh_token_valid(user_id, jti)

    def _invalidate_cached_version(self, user_id: str) -> None:
        if self._session_service:
            try:
                self._session_service._redis.delete(f"uver:{user_id}")
            except Exception:
                pass

    def delete_user(self, *, user_id: str) -> None:
        user = self.get_user_or_raise(user_id)
        persisted_user_id = str(user.id)
        self._user_repository.delete(user)
        # Stage 3: ID-based signaling
        dispatch_event(user_deleted, "auth_service", user_id=persisted_user_id)

    def revoke_token(self, jti: str, expires_at: datetime.datetime) -> None:
        """Revoke a token by adding its JTI to the blocklist."""
        self._token_repository.add_to_blocklist(jti, expires_at)
        # Also store in Mongo for long-term persistence/recovery
        if self._mongo_token_repository:
            try:
                self._mongo_token_repository.add_to_blocklist(jti, expires_at)
            except Exception:
                pass

    def is_token_revoked(self, jwt_payload: dict) -> bool:
        """
        Comprehensive check for token revocation.
        Checks Redis blocklist (primary), then fallback to Mongo if Redis is down.
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
            if self._mongo_token_repository and self._mongo_token_repository.is_jti_revoked(jti):
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
                self._session_service._redis.setex(cache_key, 300, str(user.token_version))
            except Exception:
                pass

        # If user has a token version, it must match the token's version
        if token_version is not None and user.token_version != token_version:
            return True

        return False
