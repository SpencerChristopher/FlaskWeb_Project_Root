"""
Service for managing media uploads (images) for profile and blog posts.
Optimized for Raspberry Pi: stores files on the local filesystem.
"""

from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import BinaryIO
from io import BytesIO

from PIL import Image, ImageOps


class MediaService:
    """Application service for binary asset management."""

    def __init__(self, upload_dir: str, allowed_extensions: set[str] | None = None):
        self._upload_dir = Path(upload_dir)
        self._allowed_extensions = allowed_extensions or {
            "png",
            "jpg",
            "jpeg",
            "gif",
            "webp",
        }
        self._max_size_bytes = 2 * 1024 * 1024  # 2MB Limit
        self._max_dimension_px = 1600

    def _is_allowed_file(self, filename: str) -> bool:
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self._allowed_extensions
        )

    def save_image(self, file_stream: BinaryIO, original_filename: str) -> tuple[str, str]:
        """
        Saves an image to the local filesystem.
        Returns a tuple of (relative_url, sha256_hash).
        """
        import hashlib
        if not self._is_allowed_file(original_filename):
            raise ValueError("Unsupported file extension.")

        # Enforcement: Ensure file does not exceed Pi storage limits
        file_stream.seek(0, os.SEEK_END)
        size = file_stream.tell()
        file_stream.seek(0)
        if size > self._max_size_bytes:
            raise ValueError(
                f"File too large. Maximum size is {self._max_size_bytes // 1024 // 1024}MB."
            )

        # Ensure directory exists (Defensive check)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

        # Load and normalize the image to enforce size and strip metadata
        file_stream.seek(0)
        raw = file_stream.read()
        try:
            image = Image.open(BytesIO(raw))
            image = ImageOps.exif_transpose(image)
        except Exception as exc:
            raise ValueError("Unsupported image file.") from exc

        image.thumbnail((self._max_dimension_px, self._max_dimension_px), Image.LANCZOS)

        output = BytesIO()
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            image.save(output, format="WEBP", lossless=True)
        else:
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(output, format="WEBP", quality=82, method=6)

        output.seek(0)
        final_bytes = output.read()
        if len(final_bytes) > self._max_size_bytes:
            raise ValueError("Processed image exceeds size limit.")

        # Calculate SHA-256 of the FINAL processed bytes
        file_hash = hashlib.sha256(final_bytes).hexdigest()

        # Generate UUID filename to prevent collisions and path injection
        new_filename = f"{uuid.uuid4().hex}.webp"
        file_path = self._upload_dir / new_filename

        # Save the processed file
        with open(file_path, "wb") as f:
            f.write(final_bytes)

        # Return the path relative to static and the hash
        return f"/static/uploads/{new_filename}", file_hash

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
