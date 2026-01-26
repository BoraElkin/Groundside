"""
File storage service for handling uploads and downloads.
"""
import os
import secrets
from pathlib import Path
from typing import Optional, BinaryIO
import structlog
from datetime import datetime

from config import settings

logger = structlog.get_logger()


class FileStorage:
    """
    Handles file uploads and downloads.

    For MVP, uses local filesystem. Can be extended to S3/Azure later.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize file storage.

        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path or "./uploads")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info("file_storage_initialized", path=str(self.storage_path))

    def save_file(
        self,
        file_content: bytes,
        filename: str,
        category: str = "general",
    ) -> str:
        """
        Save file to storage.

        Args:
            file_content: File content bytes
            filename: Original filename
            category: Category (penalty_notices, responses, evidence)

        Returns:
            File ID for retrieval
        """
        # Generate unique file ID
        file_id = f"{category}_{secrets.token_urlsafe(16)}"

        # Get file extension
        _, ext = os.path.splitext(filename)

        # Create category directory
        category_path = self.storage_path / category
        category_path.mkdir(exist_ok=True)

        # Save file
        file_path = category_path / f"{file_id}{ext}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(
            "file_saved",
            file_id=file_id,
            filename=filename,
            size=len(file_content),
            category=category,
        )

        return file_id

    def get_file(self, file_id: str, category: str = "general") -> Optional[bytes]:
        """
        Get file content.

        Args:
            file_id: File ID
            category: Category

        Returns:
            File content or None if not found
        """
        # Find file (try with any extension)
        category_path = self.storage_path / category

        if not category_path.exists():
            logger.warning("category_not_found", category=category)
            return None

        # Find file with this ID
        matching_files = list(category_path.glob(f"{file_id}*"))

        if not matching_files:
            logger.warning("file_not_found", file_id=file_id, category=category)
            return None

        file_path = matching_files[0]

        with open(file_path, "rb") as f:
            content = f.read()

        logger.info("file_retrieved", file_id=file_id, size=len(content))

        return content

    def get_file_path(self, file_id: str, category: str = "general") -> Optional[Path]:
        """
        Get file path.

        Args:
            file_id: File ID
            category: Category

        Returns:
            Path to file or None
        """
        category_path = self.storage_path / category

        if not category_path.exists():
            return None

        matching_files = list(category_path.glob(f"{file_id}*"))

        if not matching_files:
            return None

        return matching_files[0]

    def delete_file(self, file_id: str, category: str = "general") -> bool:
        """
        Delete file.

        Args:
            file_id: File ID
            category: Category

        Returns:
            True if deleted
        """
        file_path = self.get_file_path(file_id, category)

        if not file_path:
            logger.warning("file_not_found_for_deletion", file_id=file_id)
            return False

        file_path.unlink()

        logger.info("file_deleted", file_id=file_id)

        return True


# Global instance
file_storage = FileStorage()
