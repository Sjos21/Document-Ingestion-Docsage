from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstract storage backend for document files."""

    @abstractmethod
    async def save(self, key: str, data: bytes) -> str:
        """Persist bytes under key; return the storage path or URI."""

    @abstractmethod
    async def load(self, key: str) -> bytes:
        """Load bytes for key; raise FileNotFoundError if missing."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the object at key; no-op if already absent."""
