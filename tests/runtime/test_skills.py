"""Tests for skills system."""

import pytest
import tempfile
from pathlib import Path

from smartcp.runtime.skills import SkillLoader, SkillsAPI
from smartcp.runtime.types import UserContext


@pytest.fixture
def temp_skills_dir():
    """Create temporary skills directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def skill_loader(temp_skills_dir):
    """Create skill loader with temp directory."""
    return SkillLoader(skills_dir=temp_skills_dir)


@pytest.fixture
def user_ctx():
    """Create test user context."""
    return UserContext(user_id="test-user")


@pytest.fixture
def skills_api(skill_loader, user_ctx):
    """Create skills API."""
    return SkillsAPI(skill_loader, user_ctx)


@pytest.mark.asyncio
async def test_save_skill(skills_api):
    """Test saving a skill."""
    content = "# My Skill\n\nThis is a test skill.\n\n```python\nprint('hello')\n```\n"
    result = await skills_api.save("test_skill", content)

    assert result["status"] == "saved"
    assert result["skill"] == "test_skill"


@pytest.mark.asyncio
async def test_load_skill(skills_api):
    """Test loading a skill."""
    content = "# My Skill\n\nTest content\n"
    await skills_api.save("test_skill", content)

    result = await skills_api.load("test_skill")
    assert result["status"] == "loaded"
    assert result["content"] == content


@pytest.mark.asyncio
async def test_load_nonexistent_skill(skills_api):
    """Test loading a non-existent skill."""
    result = await skills_api.load("nonexistent")
    assert result["status"] == "not_found"


@pytest.mark.asyncio
async def test_list_skills(skills_api):
    """Test listing skills."""
    await skills_api.save("skill1", "# Skill 1\n")
    await skills_api.save("skill2", "# Skill 2\n")

    skills = await skills_api.list()
    assert "skill1" in skills
    assert "skill2" in skills


@pytest.mark.asyncio
async def test_skill_isolation(skill_loader):
    """Test that skills are isolated per user."""
    user1 = UserContext(user_id="user1")
    user2 = UserContext(user_id="user2")

    api1 = SkillsAPI(skill_loader, user1)
    api2 = SkillsAPI(skill_loader, user2)

    await api1.save("shared_name", "# User 1 skill\n")
    await api2.save("shared_name", "# User 2 skill\n")

    skill1 = await api1.load("shared_name")
    skill2 = await api2.load("shared_name")

    assert skill1["status"] == "loaded"
    assert skill2["status"] == "loaded"
    assert skill1["content"] != skill2["content"]
