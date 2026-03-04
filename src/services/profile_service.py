"""
Profile service for managing the site owner's developer identity.
Follows the 'Pydemic' style: accepting and returning Pydantic DTOs.
"""

from __future__ import annotations
import datetime
from typing import TYPE_CHECKING

from src.models.profile import Profile, WorkHistoryItem as WorkHistoryModel
from src.repositories.interfaces import ProfileRepository
from src.schemas import ProfilePublic, ProfileSchema, WorkHistoryItem as WorkHistorySchema
from typing import BinaryIO

class ProfileService:
    """Application service for developer profile orchestration."""

    def __init__(self, profile_repository: ProfileRepository, media_service: "MediaService"):
        self._profile_repository = profile_repository
        self._media_service = media_service

    def _map_work_history_to_dto(self, history: list) -> list[WorkHistorySchema]:
        return [
            WorkHistorySchema(
                company=item.company,
                role=item.role,
                start_date=item.start_date,
                end_date=item.end_date,
                location=item.location,
                description=item.description,
                skills=item.skills
            ) for item in history
        ]

    def _map_dto_to_work_history_model(self, history: list[WorkHistorySchema]) -> list[WorkHistoryModel]:
        return [
            WorkHistoryModel(
                company=item.company,
                role=item.role,
                start_date=item.start_date,
                end_date=item.end_date,
                location=item.location,
                description=item.description,
                skills=item.skills
            ) for item in history
        ]

    def get_profile(self) -> ProfilePublic:
        """
        Retrieves the profile. If none exists, returns a default one.
        """
        profile = self._profile_repository.get_profile()
        if not profile:
            # Return a default DTO if no profile exists yet
            return ProfilePublic(
                name="Developer Name",
                location="Remote / City",
                statement="Welcome to my developer profile.",
                interests=[],
                skills=[],
                social_links={},
                work_history=[],
                image_url=None,
                last_updated=None
            )
        
        return ProfilePublic(
            name=profile.name,
            location=profile.location,
            statement=profile.statement,
            interests=profile.interests,
            skills=profile.skills,
            social_links=profile.social_links,
            work_history=self._map_work_history_to_dto(profile.work_history),
            image_url=profile.image_url,
            last_updated=profile.last_updated.isoformat() if profile.last_updated else None
        )

    def update_profile(self, profile_data: ProfileSchema) -> ProfilePublic:
        """
        Updates the singleton profile. Creates it if it doesn't exist.
        """
        profile = self._profile_repository.get_profile()
        
        work_history_models = self._map_dto_to_work_history_model(profile_data.work_history)

        if not profile:
            profile = Profile(
                name=profile_data.name,
                location=profile_data.location,
                statement=profile_data.statement,
                interests=profile_data.interests,
                skills=profile_data.skills,
                social_links=profile_data.social_links.model_dump(),
                work_history=work_history_models,
                image_url=profile_data.image_url,
                last_updated=datetime.datetime.now(datetime.timezone.utc)
            )
        else:
            profile.name = profile_data.name
            profile.location = profile_data.location
            profile.statement = profile_data.statement
            profile.interests = profile_data.interests
            profile.skills = profile_data.skills
            profile.social_links = profile_data.social_links.model_dump()
            profile.work_history = work_history_models
            profile.image_url = profile_data.image_url
            profile.last_updated = datetime.datetime.now(datetime.timezone.utc)

        saved_profile = self._profile_repository.save(profile)
        
        return self.get_profile() # Returns the hydrated Public DTO

    def update_profile_photo(self, file_stream: BinaryIO, original_filename: str) -> str:
        """
        Specialized method to replace the existing profile photo with a new one.
        Ensures only one photo exists by deleting the previous file.
        """
        profile_doc = self._profile_repository.get_profile()
        
        # 1. Cleanup old photo if it exists
        if profile_doc and profile_doc.image_url:
            self._media_service.delete_image(profile_doc.image_url)

        # 2. Save new photo
        new_url = self._media_service.save_image(file_stream, original_filename)

        # 3. Update Profile reference (or create if missing)
        if not profile_doc:
            profile_doc = Profile(
                name="Developer Name",
                location="Remote / City",
                statement="Welcome to my developer profile.",
                image_url=new_url
            )
        else:
            profile_doc.image_url = new_url
            profile_doc.last_updated = datetime.datetime.now(datetime.timezone.utc)

        self._profile_repository.save(profile_doc)
        return new_url
