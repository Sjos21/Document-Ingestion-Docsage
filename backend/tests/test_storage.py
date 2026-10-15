from pathlib import Path

import pytest

from app.storage.local import LocalStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(tmp_path)


@pytest.mark.asyncio
async def test_save_and_load(storage: LocalStorage) -> None:
    key = "user-1/doc.pdf"
    data = b"%PDF-1.4 sample"

    path = await storage.save(key, data)
    assert path.endswith("doc.pdf")

    loaded = await storage.load(key)
    assert loaded == data


@pytest.mark.asyncio
async def test_load_missing_raises(storage: LocalStorage) -> None:
    with pytest.raises(FileNotFoundError):
        await storage.load("missing/file.pdf")


@pytest.mark.asyncio
async def test_delete_removes_file(storage: LocalStorage) -> None:
    key = "user-1/doc.pdf"
    await storage.save(key, b"content")
    await storage.delete(key)

    with pytest.raises(FileNotFoundError):
        await storage.load(key)


@pytest.mark.asyncio
async def test_delete_missing_is_noop(storage: LocalStorage) -> None:
    await storage.delete("does/not/exist.pdf")


@pytest.mark.asyncio
async def test_rejects_path_traversal(storage: LocalStorage) -> None:
    with pytest.raises(ValueError):
        await storage.save("../escape.txt", b"nope")
