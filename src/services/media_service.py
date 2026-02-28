"""
Service for managing media uploads (images) for profile and blog posts.
Optimized for Raspberry Pi: stores files on the local filesystem.
"""

from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import BinaryIO
from werkzeug.utils import secure_filename

class MediaService:
    """Application service for binary asset management."""

    def __init__(self, upload_dir: str, allowed_extensions: set[str] | None = None):
        self._upload_dir = Path(upload_dir)
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

        # Enforcement: Ensure file does not exceed Pi storage limits
        file_stream.seek(0, os.SEEK_END)
        size = file_stream.tell()
        file_stream.seek(0)
        if size > self._max_size_bytes:
            raise ValueError(f"File too large. Maximum size is {self._max_size_bytes // 1024 // 1024}MB.")

        # Ensure directory exists (Defensive check)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate UUID filename to prevent collisions and path injection
        ext = original_filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        
        file_path = self._upload_dir / new_filename
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_stream.read())

        # Return the path relative to static
        return f"/static/uploads/{new_filename}"

    def delete_image(self, image_url: str) -> bool:
        """
        Deletes an image file from the filesystem based on its relative URL path.
        Returns True if successful, False otherwise.
        """
        if not image_url or not image_url.startswith("/static/uploads/"):
            return False
        
        # Extract filename and resolve to absolute path
        filename = image_url.replace("/static/uploads/", "")
        file_path = (self._upload_dir / filename).resolve()

        # Security Check: Ensure the file is actually within the intended upload directory
        if not str(file_path).startswith(str(self._upload_dir.resolve())):
            return False

        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
        except Exception:
            # Silent failure to prevent blocking business logic
            return False
        return False
