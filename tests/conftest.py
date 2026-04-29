import os
import pytest
from pathlib import Path
from nemoguardrails import RailsConfig, LLMRails

os.environ.setdefault("OPENAI_API_KEY", "sk-fake")

@pytest.fixture(scope="session")
def project_root():
    return Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def rails(project_root):
    config_path = project_root / "config"
    config = RailsConfig.from_path(str(config_path))
    return LLMRails(config)
