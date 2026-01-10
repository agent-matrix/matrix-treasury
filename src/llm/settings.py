"""
LLM Provider Settings Management

Supports multiple LLM providers for the CFO intelligence:
- Ollama (default, local, no API key needed)
- OpenAI (GPT-4, GPT-4-turbo)
- Claude (Anthropic)
- WatsonX.ai (IBM)

Settings are loaded from environment variables and can be updated via API.
"""

import enum
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file
load_dotenv()

CONFIG_DIR = Path.home() / ".matrix-treasury"
CONFIG_FILE = CONFIG_DIR / "llm_settings.json"


class LLMProvider(str, enum.Enum):
    """Supported LLM providers."""
    ollama = "ollama"
    openai = "openai"
    claude = "claude"
    watsonx = "watsonx"


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4o-mini")
    base_url: str = Field(default="")  # Optional: for Azure OpenAI or proxies
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=2048)


class ClaudeConfig(BaseModel):
    """Anthropic Claude API configuration."""
    api_key: str = Field(default="")
    model: str = Field(default="claude-sonnet-4-5")
    base_url: str = Field(default="")  # Optional: for proxies
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=2048)


class WatsonxConfig(BaseModel):
    """IBM WatsonX.ai API configuration."""
    api_key: str = Field(default="")
    project_id: str = Field(default="")
    model_id: str = Field(default="ibm/granite-3-8b-instruct")
    base_url: str = Field(default="https://us-south.ml.cloud.ibm.com")
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=1024)


class OllamaConfig(BaseModel):
    """Ollama local LLM configuration."""
    base_url: str = Field(default="http://localhost:11434")
    model: str = Field(default="llama3")
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=2048)


class LLMSettings(BaseModel):
    """Main LLM configuration settings."""
    provider: LLMProvider = Field(default=LLMProvider.ollama)

    # Provider-specific configs
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    watsonx: WatsonxConfig = Field(default_factory=WatsonxConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

    @classmethod
    def from_env(cls) -> "LLMSettings":
        """
        Load settings from environment variables.

        Environment variables take precedence over saved settings.
        """
        # Load saved settings if exist
        if CONFIG_FILE.exists():
            import json
            data = json.loads(CONFIG_FILE.read_text("utf-8"))
            settings = cls.model_validate(data)
        else:
            settings = cls()

        # Override with environment variables
        env_provider = os.getenv("CFO_PROVIDER", os.getenv("LLM_PROVIDER"))
        if env_provider:
            try:
                settings.provider = LLMProvider(env_provider.lower())
            except ValueError:
                pass  # Invalid provider, keep existing

        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            settings.openai.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("CFO_OPENAI_MODEL"):
            settings.openai.model = os.getenv("CFO_OPENAI_MODEL")
        if os.getenv("OPENAI_BASE_URL"):
            settings.openai.base_url = os.getenv("OPENAI_BASE_URL")

        # Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            settings.claude.api_key = os.getenv("ANTHROPIC_API_KEY")
        if os.getenv("CFO_CLAUDE_MODEL"):
            settings.claude.model = os.getenv("CFO_CLAUDE_MODEL")
        if os.getenv("ANTHROPIC_BASE_URL"):
            settings.claude.base_url = os.getenv("ANTHROPIC_BASE_URL")

        # WatsonX
        if os.getenv("WATSONX_API_KEY"):
            settings.watsonx.api_key = os.getenv("WATSONX_API_KEY")
        if os.getenv("WATSONX_PROJECT_ID"):
            settings.watsonx.project_id = os.getenv("WATSONX_PROJECT_ID")
        if os.getenv("CFO_WATSONX_MODEL"):
            settings.watsonx.model_id = os.getenv("CFO_WATSONX_MODEL")
        if os.getenv("WATSONX_BASE_URL"):
            settings.watsonx.base_url = os.getenv("WATSONX_BASE_URL")

        # Ollama
        if os.getenv("OLLAMA_BASE_URL"):
            settings.ollama.base_url = os.getenv("OLLAMA_BASE_URL")
        if os.getenv("CFO_OLLAMA_MODEL"):
            settings.ollama.model = os.getenv("CFO_OLLAMA_MODEL")

        return settings

    def save(self) -> None:
        """Save settings to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(self.model_dump_json(indent=2), "utf-8")

    def get_active_config(self):
        """Get the configuration for the active provider."""
        if self.provider == LLMProvider.openai:
            return self.openai
        elif self.provider == LLMProvider.claude:
            return self.claude
        elif self.provider == LLMProvider.watsonx:
            return self.watsonx
        elif self.provider == LLMProvider.ollama:
            return self.ollama
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


# Global settings instance
_settings = LLMSettings.from_env()


def get_llm_settings() -> LLMSettings:
    """Get the global LLM settings instance."""
    return _settings


def set_provider(provider: LLMProvider) -> LLMSettings:
    """Set the active LLM provider."""
    _settings.provider = provider
    _settings.save()
    return _settings


def update_settings(updates: dict) -> LLMSettings:
    """Update settings with partial or full configuration."""
    global _settings

    # Update provider if present
    if "provider" in updates:
        _settings.provider = LLMProvider(updates["provider"])

    # Update provider-specific configs
    if "openai" in updates:
        _settings.openai = OpenAIConfig(**updates["openai"])
    if "claude" in updates:
        _settings.claude = ClaudeConfig(**updates["claude"])
    if "watsonx" in updates:
        _settings.watsonx = WatsonxConfig(**updates["watsonx"])
    if "ollama" in updates:
        _settings.ollama = OllamaConfig(**updates["ollama"])

    _settings.save()
    return _settings
