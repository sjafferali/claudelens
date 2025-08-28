"""Unit tests for data ownership without database."""

import pytest

from app.models.user import UserRole


@pytest.mark.asyncio
async def test_no_viewer_role_allowed():
    """Test that viewer role is no longer accepted."""

    # Should not have VIEWER in enum
    assert not hasattr(UserRole, "VIEWER")

    # Should only have ADMIN and USER
    assert UserRole.ADMIN == "admin"
    assert UserRole.USER == "user"

    # Verify enum values
    valid_roles = list(UserRole)
    assert len(valid_roles) == 2
    assert UserRole.ADMIN in valid_roles
    assert UserRole.USER in valid_roles
