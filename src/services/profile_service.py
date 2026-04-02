"""
Profile service for managing the site owner's developer identity.

Responsibilities:
- Orchestrate profile reads/updates as a singleton document.
- Validate and normalize inbound data (including social links and image URL rules).
- Coordinate image lifecycle via MediaService to avoid orphaned uploads.
- Return Pydantic DTOs for consistent API responses.
"""

import datetime
import logging
import re
from typing import TYPE_CHECKING, BinaryIO

from src.models.profile import Profile, WorkHistoryItem as WorkHistoryModel
from src.repositories.interfaces import ProfileRepository
from src.schemas import (
    ProfilePublic,
    ProfileSchema,
    WorkHistoryItem as WorkHistorySchema,
)
from src.exceptions import BadRequestException

if TYPE_CHECKING:
    from src.services.media_service import MediaService
    from src.schemas import UserIdentity

logger = logging.getLogger(__name__)


class ProfileService:
    """Application service for developer profile orchestration.

    This service mediates profile persistence, validation, and media lifecycle
    coordination. It keeps the profile consistent as a singleton and ensures
    image metadata is managed server-side to avoid leakage and orphaned files.
    """

    def __init__(
        self, profile_repository: ProfileRepository, media_service: "MediaService"
    ):
        self._profile_repository = profile_repository
        self._media_service = media_service

    def _map_work_history_to_dto(self, history: list) -> list[WorkHistorySchema]:
        """Convert profile work history models into DTOs.

        Args:
            history: List of WorkHistoryModel instances from persistence.

        Returns:
            list[WorkHistorySchema]: DTOs suitable for API responses.
        """
        return [
            WorkHistorySchema(
                company=item.company,
                role=item.role,
                start_date=item.start_date,
                end_date=item.end_date,
                location=item.location,
                description=item.description,
                skills=item.skills,
            )
            for item in history
        ]

    def _map_dto_to_work_history_model(
        self, history: list[WorkHistorySchema]
    ) -> list[WorkHistoryModel]:
        """Convert inbound work history DTOs into persistence models.

        Args:
            history: List of validated WorkHistorySchema DTOs.

        Returns:
            list[WorkHistoryModel]: Embedded document models for persistence.
        """
        return [
            WorkHistoryModel(
                company=item.company,
                role=item.role,
                start_date=item.start_date,
                end_date=item.end_date,
                location=item.location,
                description=item.description,
                skills=item.skills,
            )
            for item in history
        ]

    def _normalize_social_links(self, links: dict[str, str]) -> dict[str, str]:
        """Normalize social link keys into a consistent slug format.

        Args:
            links: Mapping of social platform keys to URLs.

        Returns:
            dict[str, str]: Normalized key/value mapping with cleaned URLs.
        """
        normalized: dict[str, str] = {}
        for key, url in links.items():
            norm_key = re.sub(r"[\\s_]+", "-", key.strip().lower())
            if not norm_key:
                continue
            if url:
                normalized[norm_key] = url.strip()
        return normalized

    def _validate_image_url(self, image_url: str | None) -> str | None:
        """Validate a profile image URL is a local upload.

        Args:
            image_url: Candidate image URL from a client request.

        Returns:
            str | None: Validated URL or None if empty.

        Raises:
            BadRequestException: If the URL does not reference local uploads.
        """
        if not image_url:
            return None
        if not image_url.startswith("/static/uploads/"):
            raise BadRequestException(
                "Profile image URL must reference a local upload."
            )
        return image_url

    def get_profile(self) -> ProfilePublic:
        """Retrieve the profile singleton or return a default profile.

        Returns:
            ProfilePublic: The profile DTO for public use.
        """
        profile = self._profile_repository.get_profile()
        if not profile:
            # Return a default DTO if no profile exists yet
            return ProfilePublic(
                name="Developer Name",
                headline_role=None,
                location="Remote / City",
                statement="Welcome to my developer profile.",
                interests=[],
                skills=[],
                social_links={},
                work_history=[],
                image_url=None,
                last_updated=None,
            )

        return ProfilePublic(
            name=profile.name,
            headline_role=profile.headline_role,
            location=profile.location,
            statement=profile.statement,
            interests=profile.interests,
            skills=profile.skills,
            social_links=profile.social_links or {},
            work_history=self._map_work_history_to_dto(profile.work_history),
            image_url=profile.image_url,
            last_updated=(
                profile.last_updated.isoformat() if profile.last_updated else None
            ),
        )

    def update_profile(
        self, profile_data: ProfileSchema, user: "UserIdentity"
    ) -> ProfilePublic:
        """Update the singleton profile, creating it if missing.

        Handles image URL changes and ensures any replaced image is deleted to
        prevent orphaned media.

        Args:
            profile_data: Validated profile payload.
            user: The authenticated user performing the update.

        Returns:
            ProfilePublic: Updated profile DTO.

        Raises:
            BadRequestException: If an image URL is invalid.
        """
        profile = self._profile_repository.get_profile()

        work_history_models = self._map_dto_to_work_history_model(
            profile_data.work_history
        )
        normalized_social_links = self._normalize_social_links(
            profile_data.social_links
        )
        desired_image_url = self._validate_image_url(profile_data.image_url)

        if not profile:
            profile = Profile(
                name=profile_data.name,
                headline_role=profile_data.headline_role,
                location=profile_data.location,
                statement=profile_data.statement,
                interests=profile_data.interests,
                skills=profile_data.skills,
                social_links=normalized_social_links,
                work_history=work_history_models,
                image_url=desired_image_url,
                image_hash=None,
                image_filename=None,
                image_uploaded_at=None,
                last_updated=datetime.datetime.now(datetime.timezone.utc),
            )
        else:
            profile.name = profile_data.name
            profile.headline_role = profile_data.headline_role
            profile.location = profile_data.location
            profile.statement = profile_data.statement
            profile.interests = profile_data.interests
            profile.skills = profile_data.skills
            profile.social_links = normalized_social_links
            profile.work_history = work_history_models

            if profile_data.image_url and profile_data.image_url != profile.image_url:
                if profile.image_url:
                    self._media_service.delete_image(profile.image_url)
                profile.image_url = self._validate_image_url(profile_data.image_url)
                profile.image_hash = None
                profile.image_filename = None
                profile.image_uploaded_at = None
            elif not profile_data.image_url and profile.image_url:
                # If image_url is explicitly cleared, delete the old file
                self._media_service.delete_image(profile.image_url)
                profile.image_url = None
                profile.image_hash = None
                profile.image_filename = None
                profile.image_uploaded_at = None
            profile.last_updated = datetime.datetime.now(datetime.timezone.utc)

        saved_profile = self._profile_repository.save(profile)
        logger.info(
            f"Developer profile updated by user: {user.username} (ID: {user.id})"
        )

        return self.get_profile()  # Returns the hydrated Public DTO

    def update_profile_photo(
        self, file_stream: BinaryIO, original_filename: str, user: "UserIdentity"
    ) -> str:
        """Replace the profile photo with a newly uploaded image.

        Deletes any existing image to prevent orphaned files. Stores hash,
        original filename, and upload timestamp for traceability.

        Args:
            file_stream: Binary stream of the image upload.
            original_filename: Original filename provided by the client.
            user: The authenticated user performing the upload.

        Returns:
            str: URL of the stored image.

        Raises:
            ValueError: If the image is invalid or violates size/format rules.
        """
        profile_doc = self._profile_repository.get_profile()

        # 1. Cleanup old photo if it exists
        if profile_doc and profile_doc.image_url:
            self._media_service.delete_image(profile_doc.image_url)

        # 2. Save new photo (returns URL and SHA-256 hash)
        new_url, file_hash = self._media_service.save_image(
            file_stream, original_filename
        )

        # 3. Update Profile reference (or create if missing)
        if not profile_doc:
            profile_doc = Profile(
                name="Developer Name",
                location="Remote / City",
                statement="Welcome to my developer profile.",
                image_url=new_url,
                image_hash=file_hash,
                image_filename=original_filename,
                image_uploaded_at=datetime.datetime.now(datetime.timezone.utc),
            )
        else:
            profile_doc.image_url = new_url
            profile_doc.image_hash = file_hash
            profile_doc.image_filename = original_filename
            profile_doc.image_uploaded_at = datetime.datetime.now(datetime.timezone.utc)
            profile_doc.last_updated = datetime.datetime.now(datetime.timezone.utc)

        self._profile_repository.save(profile_doc)
        logger.info(
            f"Profile photo replaced by user: {user.username} (ID: {user.id}). URL: {new_url}"
        )
        return new_url
