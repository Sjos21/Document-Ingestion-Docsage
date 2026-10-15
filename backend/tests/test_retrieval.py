"""Service-level retrieval tests against REAL Postgres+pgvector.

Skipped automatically if Postgres is unreachable (e.g. docker compose not
running) -- this suite intentionally cannot run against SQLite because
cosine_distance() requires the pgvector <=> operator.
"""
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import Chunk, Document, User
from app.services.retrieval import search_chunks

PG_TEST_URL = "postgresql+asyncpg://docsage:docsage@localhost:5432/docsage"


@pytest.fixture
async def pg_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(PG_TEST_URL)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pytest.skip("Postgres not reachable at localhost:5432 -- run docker compose up -d postgres")

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()  # never persist test data into dev DB

    await engine.dispose()


@pytest.fixture
async def pg_user(pg_session: AsyncSession) -> User:
    import uuid

    user = User(email=f"retrieval_test_{uuid.uuid4()}@example.com", hashed_password="x")
    pg_session.add(user)
    await pg_session.flush()
    return user


async def _make_indexed_document(session: AsyncSession, user: User, filename: str, chunks: list[tuple[str, list[float]]]) -> Document:
    document = Document(
        user_id=user.id,
        filename=filename,
        content_hash=filename,
        storage_path=f"/tmp/{filename}",
        status="indexed",
    )
    session.add(document)
    await session.flush()

    for content, vector in chunks:
        session.add(
            Chunk(
                document_id=document.id,
                content=content,
                embedding=vector,
                token_count=len(content.split()),
                embedding_model_version="test",
            )
        )
    await session.flush()
    return document


@pytest.mark.asyncio
async def test_search_returns_most_similar_chunk_first(pg_session: AsyncSession, pg_user: User) -> None:
    from app.services.embedding import embed_texts

    close_vec, far_vec, query_vec = embed_texts(["cats are great pets", "quarterly tax filing deadlines", "cats are wonderful pets"])

    await _make_indexed_document(
        pg_session, pg_user, "pets.pdf",
        [("cats are great pets", close_vec), ("quarterly tax filing deadlines", far_vec)],
    )

    results = await search_chunks(session=pg_session, user_id=pg_user.id, query="cats are wonderful pets", top_k=2)

    assert len(results) == 2
    assert results[0].content == "cats are great pets"
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_search_excludes_non_indexed_documents(pg_session: AsyncSession, pg_user: User) -> None:
    from app.services.embedding import embed_texts

    vec = embed_texts(["draft content not yet indexed"])[0]
    document = Document(
        user_id=pg_user.id, filename="draft.pdf", content_hash="draft",
        storage_path="/tmp/draft.pdf", status="processing",
    )
    pg_session.add(document)
    await pg_session.flush()
    pg_session.add(Chunk(document_id=document.id, content="draft content not yet indexed", embedding=vec, token_count=4, embedding_model_version="test"))
    await pg_session.flush()

    results = await search_chunks(session=pg_session, user_id=pg_user.id, query="draft content", top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_search_scoped_to_requesting_user_only(pg_session: AsyncSession, pg_user: User) -> None:
    import uuid

    from app.services.embedding import embed_texts

    other_user = User(email=f"other_{uuid.uuid4()}@example.com", hashed_password="x")
    pg_session.add(other_user)
    await pg_session.flush()

    vec = embed_texts(["secret content belonging to another user"])[0]
    await _make_indexed_document(pg_session, other_user, "other.pdf", [("secret content belonging to another user", vec)])

    results = await search_chunks(session=pg_session, user_id=pg_user.id, query="secret content", top_k=5)
    assert results == []

@pytest.mark.asyncio
async def test_search_returns_empty_when_user_has_no_documents(
    pg_session: AsyncSession, pg_user: User
) -> None:
    results = await search_chunks(session=pg_session, user_id=pg_user.id, query="anything", top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_search_returns_empty_when_user_has_no_documents(
    pg_session: AsyncSession, pg_user: User
) -> None:
    results = await search_chunks(session=pg_session, user_id=pg_user.id, query="anything", top_k=5)
    assert results == []


@pytest.mark.asyncio
async def test_hybrid_search_finds_exact_keyword_match(
    pg_session: AsyncSession, pg_user: User
) -> None:
    """BM25 leg should surface an exact term even if the vector leg alone
    would rank it lower -- the reason hybrid search exists per architecture.md."""
    from app.services.embedding import embed_texts

    invoice_vec, unrelated_vec = embed_texts(
        ["invoice number INV-88213 payment due", "a paragraph about gardening tips"]
    )

    await _make_indexed_document(
        pg_session, pg_user, "invoice.pdf",
        [("invoice number INV-88213 payment due", invoice_vec)],
    )
    await _make_indexed_document(
        pg_session, pg_user, "garden.pdf",
        [("a paragraph about gardening tips", unrelated_vec)],
    )

    results = await search_chunks(session=pg_session, user_id=pg_user.id, query="INV-88213", top_k=3)

    assert len(results) >= 1
    assert any("INV-88213" in r.content for r in results)
