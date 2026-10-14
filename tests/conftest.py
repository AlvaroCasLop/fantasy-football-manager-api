import pytest
from httpx import ASGITransport, AsyncClient

from src.app.main import app


@pytest.fixture
async def client():
    """Async test client using ASGI transport (no real network server needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
