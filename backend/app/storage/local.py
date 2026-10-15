import asyncio
from pathlib import Path

from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """Filesystem-backed storage for local deployments."""

    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)

    def _resolve(self, key: str) -> Path:
        normalized = Path(key)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError(f"Invalid storage key: {key}")
        return self._base_path / normalized

    async def save(self, key: str, data: bytes) -> str:
        path = self._resolve(key)

        def _write() -> str:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return str(path)

        return await asyncio.to_thread(_write)

    async def load(self, key: str) -> bytes:
        path = self._resolve(key)

        def _read() -> bytes:
            if not path.is_file():
                raise FileNotFoundError(f"Storage object not found: {key}")
            return path.read_bytes()

        return await asyncio.to_thread(_read)

    async def delete(self, key: str) -> None:
        path = self._resolve(key)

        def _remove() -> None:
            if path.is_file():
                path.unlink()

        await asyncio.to_thread(_remove)
