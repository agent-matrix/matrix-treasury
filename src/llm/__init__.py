"""
LLM Provider Module

Manages multi-provider LLM support for the Matrix Treasury CFO.
"""

from .settings import (
    LLMProvider,
    LLMSettings,
    OpenAIConfig,
    ClaudeConfig,
    WatsonxConfig,
    OllamaConfig,
    get_llm_settings,
    set_provider,
    update_settings,
)
from .provider import build_llm, test_llm_connection

__all__ = [
    "LLMProvider",
    "LLMSettings",
    "OpenAIConfig",
    "ClaudeConfig",
    "WatsonxConfig",
    "OllamaConfig",
    "get_llm_settings",
    "set_provider",
    "update_settings",
    "build_llm",
    "test_llm_connection",
]
