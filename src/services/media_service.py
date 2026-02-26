"""
Service for managing media uploads (images) for profile and blog posts.
Optimized for Raspberry Pi: stores files on the local filesystem.
"""

from __future__ import annotations
import os
import uuid
from typing import BinaryIO
from werkzeug.utils import secure_filename

class MediaService:
    """Application service for binary asset management."""

    def __init__(self, upload_dir: str, allowed_extensions: set[str] | None = None):
        self._upload_dir = upload_dir
        self._allowed_extensions = allowed_extensions or {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self._max_size_bytes = 2 * 1024 * 1024 # 2MB Limit

    def _is_allowed_file(self, filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self._allowed_extensions

    def save_image(self, file_stream: BinaryIO, original_filename: str) -> str:
        """
        Saves an image to the local filesystem and returns the relative URL path.
        """
        if not self._is_allowed_file(original_filename):
            raise ValueError("Unsupported file extension.")

        # Ensure directory exists (Defensive check)
        os.makedirs(self._upload_dir, exist_ok=True)

        # Generate UUID filename to prevent collisions and path injection
        ext = original_filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        
        file_path = os.path.join(self._upload_dir, new_filename)
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_stream.read())

        # Return the path relative to static
        return f"/static/uploads/{new_filename}"
