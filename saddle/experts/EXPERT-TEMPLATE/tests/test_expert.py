"""
Tests for {{EXPERT_NAME}} Expert

Run with: pytest tests/test_expert.py -v
Or via: ./scripts/test-expert.sh {{expert_name}}
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

EXPERT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = EXPERT_ROOT / "mcp-server" / "config.yaml"


@pytest.fixture
def config():
    """Load expert configuration."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


class TestKnowledgeFiles:
    """Test knowledge base structure and content."""

    def test_skill_md_exists(self):
        """SKILL.md must exist."""
        skill_path = EXPERT_ROOT / "SKILL.md"
        assert skill_path.exists(), "SKILL.md not found"

    def test_core_knowledge_exists(self):
        """Core knowledge directory must have content."""
        core_path = EXPERT_ROOT / "knowledge" / "core"
        assert core_path.exists(), "knowledge/core/ not found"
        # Allow .gitkeep or actual content
        files = list(core_path.glob("*"))
        assert len(files) > 0, "knowledge/core/ is empty"

    def test_knowledge_directories_exist(self):
        """All knowledge directories must exist."""
        knowledge_path = EXPERT_ROOT / "knowledge"
        required_dirs = ["core", "reference", "org-patterns", "decision-log"]
        for dir_name in required_dirs:
            dir_path = knowledge_path / dir_name
            assert dir_path.exists(), f"knowledge/{dir_name}/ not found"

    def test_token_budget(self, config):
        """Core knowledge should be under token budget."""
        # Approximate token count (1 token ~ 4 chars)
        max_tokens = 4000
        max_chars = max_tokens * 4

        total_chars = 0

        # Count SKILL.md
        skill_path = EXPERT_ROOT / "SKILL.md"
        if skill_path.exists():
            total_chars += len(skill_path.read_text())

        # Count core knowledge
        for pattern in config["knowledge"]["core_files"]:
            for path in EXPERT_ROOT.glob(pattern):
                if path.is_file() and path.suffix == ".md":
                    total_chars += len(path.read_text())

        estimated_tokens = total_chars / 4
        assert total_chars <= max_chars, (
            f"Core knowledge exceeds token budget: "
            f"~{estimated_tokens:.0f} tokens (max {max_tokens})"
        )


class TestConfiguration:
    """Test expert configuration."""

    def test_config_exists(self):
        """Configuration file must exist."""
        assert CONFIG_PATH.exists(), "mcp-server/config.yaml not found"

    def test_config_valid_yaml(self, config):
        """Configuration must be valid YAML."""
        assert config is not None, "Config is empty"

    def test_config_has_required_fields(self, config):
        """Configuration must have all required fields."""
        required_fields = ["expert", "llm", "knowledge", "server"]
        for field in required_fields:
            assert field in config, f"Missing required config field: {field}"

    def test_expert_name_set(self, config):
        """Expert name must be configured."""
        expert_name = config["expert"]["name"]
        assert expert_name != "{{EXPERT_NAME}}", "Expert name not configured (still has placeholder)"
        assert expert_name, "Expert name is empty"

    def test_llm_config_valid(self, config):
        """LLM configuration must be valid."""
        llm_config = config["llm"]
        assert "provider" in llm_config, "LLM provider not specified"
        assert "model" in llm_config, "LLM model not specified"
        assert 0 <= llm_config.get("temperature", 0.2) <= 1, "Temperature out of range"

    def test_port_unique(self, config):
        """Server port must be configured."""
        port = config["server"]["port"]
        assert port != "{{PORT}}", "Port not configured (still has placeholder)"
        assert isinstance(port, int), "Port must be an integer"
        assert 1024 <= port <= 65535, "Port out of valid range"


class TestServerModule:
    """Test server module structure."""

    def test_server_py_exists(self):
        """Server implementation must exist."""
        server_path = EXPERT_ROOT / "mcp-server" / "server.py"
        assert server_path.exists(), "mcp-server/server.py not found"

    def test_requirements_exists(self):
        """Requirements file must exist."""
        req_path = EXPERT_ROOT / "mcp-server" / "requirements.txt"
        assert req_path.exists(), "mcp-server/requirements.txt not found"

    def test_server_imports(self):
        """Server module must have valid imports."""
        server_path = EXPERT_ROOT / "mcp-server" / "server.py"
        content = server_path.read_text()

        # Check for essential imports
        assert "from mcp.server import Server" in content, "Missing MCP Server import"
        assert "from anthropic import Anthropic" in content, "Missing Anthropic import"

    def test_server_syntax_valid(self):
        """Server module must have valid Python syntax."""
        server_path = EXPERT_ROOT / "mcp-server" / "server.py"
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(server_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error in server.py: {result.stderr}"


class TestBoundaries:
    """Test expert boundary handling."""

    def test_boundaries_configured(self, config):
        """Boundaries should be configured."""
        assert "boundaries" in config, "No boundaries configured"

    def test_redirect_configured(self, config):
        """Redirect behavior should be configured."""
        boundaries = config.get("boundaries", {})
        redirect = boundaries.get("redirect_to", {})
        assert "main_agent" in redirect, "No main_agent redirect configured"


class TestReadme:
    """Test documentation."""

    def test_readme_exists(self):
        """Expert README must exist."""
        readme_path = EXPERT_ROOT / "README.md"
        assert readme_path.exists(), "README.md not found"

    def test_readme_customized(self):
        """README must be customized from template."""
        readme_path = EXPERT_ROOT / "README.md"
        content = readme_path.read_text()
        assert "{{EXPERT_NAME}}" not in content, "README still has placeholder values"


# Integration tests (require running server)
class TestIntegration:
    """Integration tests - run with --run-integration flag."""

    @pytest.mark.integration
    def test_server_starts(self):
        """Server should start without errors."""
        # This would require actually starting the server
        # Placeholder for integration test
        pytest.skip("Integration test - run with live server")

    @pytest.mark.integration
    def test_consult_responds(self):
        """Consult tool should respond."""
        pytest.skip("Integration test - run with live server")

    @pytest.mark.integration
    def test_boundary_handling(self):
        """Out-of-domain queries should be rejected."""
        pytest.skip("Integration test - run with live server")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
