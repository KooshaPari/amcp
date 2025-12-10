"""Unit tests for SkillsAPI."""

import pytest
import tempfile
from pathlib import Path

from smartcp.runtime.skills.api import SkillsAPI
from smartcp.runtime.skills.loader import SkillLoader
from smartcp.runtime.types import UserContext


class TestSkillsAPI:
    """Unit tests for SkillsAPI."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """Create a skill loader."""
        return SkillLoader(skills_dir=str(temp_dir))

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def skills_api(self, loader, user_ctx):
        """Create a skills API."""
        return SkillsAPI(loader, user_ctx)

    @pytest.mark.asyncio
    async def test_load(self, skills_api):
        """Test loading a skill."""
        await skills_api.save("test_skill", "# Test Skill\n\nContent.")

        result = await skills_api.load("test_skill")
        assert result["status"] == "loaded"
        assert "Content." in result["content"]

    @pytest.mark.asyncio
    async def test_save(self, skills_api):
        """Test saving a skill."""
        result = await skills_api.save("new_skill", "# New Skill")
        assert result["status"] == "saved"

    @pytest.mark.asyncio
    async def test_list(self, skills_api):
        """Test listing skills."""
        await skills_api.save("skill1", "Content 1")
        await skills_api.save("skill2", "Content 2")

        skills = await skills_api.list()
        assert set(skills) == {"skill1", "skill2"}
