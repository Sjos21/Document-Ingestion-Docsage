from app.services.chunking import chunk_text


def test_chunk_text_empty_returns_empty_list() -> None:
    assert chunk_text("") == []


def test_chunk_text_single_chunk_when_short() -> None:
    text = " ".join(["word"] * 100)
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0].token_count == 100


def test_chunk_text_overlap_boundaries() -> None:
    words = [f"w{i}" for i in range(1200)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    assert len(chunks) == 3
    assert chunks[0].token_count == 500
    # second chunk starts 450 words in (step = 500 - 50)
    assert chunks[1].content.split()[0] == "w450"


def test_chunk_text_rejects_invalid_overlap() -> None:
    import pytest

    with pytest.raises(ValueError):
        chunk_text("a b c", chunk_size=10, overlap=10)