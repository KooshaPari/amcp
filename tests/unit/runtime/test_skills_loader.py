"""Unit tests for SkillLoader."""

import pytest
import tempfile
from pathlib import Path

from smartcp.runtime.skills.loader import SkillLoader
from smartcp.runtime.types import UserContext


class TestSkillLoader:
    """Unit tests for SkillLoader."""

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

    @pytest.mark.asyncio
    async def test_save_and_load(self, loader, user_ctx):
        """Test saving and loading a skill."""
        content = "# My Skill\n\nThis is a test skill."
        result = await loader.save("test_skill", content, user_ctx)

        assert result["status"] == "saved"

        loaded = await loader.load("test_skill", user_ctx)
        assert loaded["status"] == "loaded"
        assert loaded["content"] == content

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, loader, user_ctx):
        """Test loading a non-existent skill."""
        result = await loader.load("nonexistent", user_ctx)
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_list_skills(self, loader, user_ctx):
        """Test listing skills."""
        await loader.save("skill1", "Content 1", user_ctx)
        await loader.save("skill2", "Content 2", user_ctx)

        skills = await loader.list(user_ctx)
        assert set(skills) == {"skill1", "skill2"}

    @pytest.mark.asyncio
    async def test_user_isolation(self, loader):
        """Test that skills are isolated by user."""
        user1 = UserContext(user_id="user1")
        user2 = UserContext(user_id="user2")

        await loader.save("skill1", "User1 content", user1)
        await loader.save("skill1", "User2 content", user2)

        loaded1 = await loader.load("skill1", user1)
        loaded2 = await loader.load("skill1", user2)

        assert loaded1["content"] == "User1 content"
        assert loaded2["content"] == "User2 content"
