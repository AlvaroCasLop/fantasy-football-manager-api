import pytest
from httpx import AsyncClient

from src.app.core.security import verify_supabase_token


def test_verify_supabase_token_unverified_dev():
    # In development mode, verify_supabase_token can handle tokens gracefully
    user = verify_supabase_token("dummy.token.here")
    assert user.id is not None
