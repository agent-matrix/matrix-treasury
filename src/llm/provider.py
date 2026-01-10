"""
LLM Provider Factory

Creates configured LLM instances for CrewAI based on active provider settings.
Handles authentication, model selection, and connection management.
"""

import os
import logging
from crewai import LLM
from .settings import LLMProvider, get_llm_settings

logger = logging.getLogger(__name__)


def build_llm() -> LLM:
    """
    Return an initialized CrewAI LLM using the active provider.

    Raises:
        ValueError: If required credentials are missing
    """
    settings = get_llm_settings()
    provider = settings.provider

    logger.info(f"Building LLM for provider: {provider}")

    if provider == LLMProvider.openai:
        # Use settings config if available, otherwise fall back to env vars
        api_key = settings.openai.api_key or os.getenv("OPENAI_API_KEY", "")
        model = settings.openai.model or os.getenv("CFO_OPENAI_MODEL", "gpt-4o-mini")
        base_url = settings.openai.base_url or os.getenv("OPENAI_BASE_URL", "")

        # Validate required credentials
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. "
                "Set OPENAI_API_KEY environment variable or configure in settings."
            )

        # Ensure model has provider prefix for CrewAI
        if not model.startswith("openai/"):
            model = f"openai/{model}"

        logger.info(f"Using OpenAI model: {model}")
        return LLM(
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
            temperature=settings.openai.temperature,
            max_tokens=settings.openai.max_tokens,
        )

    if provider == LLMProvider.claude:
        # Use settings config if available, otherwise fall back to env vars
        api_key = settings.claude.api_key or os.getenv("ANTHROPIC_API_KEY", "")
        model = settings.claude.model or os.getenv("CFO_CLAUDE_MODEL", "claude-sonnet-4-5")
        base_url = settings.claude.base_url or os.getenv("ANTHROPIC_BASE_URL", "")

        # Validate required credentials
        if not api_key:
            raise ValueError(
                "Claude API key is required. "
                "Set ANTHROPIC_API_KEY environment variable or configure in settings."
            )

        # CRITICAL: Set API key as environment variable (required by CrewAI's native Anthropic provider)
        # CrewAI's Anthropic integration checks for this env var internally
        os.environ["ANTHROPIC_API_KEY"] = api_key

        # Optional: Set base URL as environment variable if provided
        if base_url:
            os.environ["ANTHROPIC_BASE_URL"] = base_url

        # Ensure model has provider prefix for CrewAI
        if not model.startswith("anthropic/"):
            model = f"anthropic/{model}"

        logger.info(f"Using Claude model: {model}")
        return LLM(
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
            temperature=settings.claude.temperature,
            max_tokens=settings.claude.max_tokens,
        )

    if provider == LLMProvider.watsonx:
        # Use settings config with proper watsonx.ai integration
        api_key = settings.watsonx.api_key or os.getenv("WATSONX_API_KEY", "")
        project_id = settings.watsonx.project_id or os.getenv("WATSONX_PROJECT_ID", "")
        model = settings.watsonx.model_id or os.getenv(
            "CFO_WATSONX_MODEL",
            "ibm/granite-3-8b-instruct",  # Default model (without prefix)
        )
        base_url = settings.watsonx.base_url or os.getenv(
            "WATSONX_BASE_URL",
            "https://us-south.ml.cloud.ibm.com",  # Default to US South
        )

        # Validate required credentials
        if not api_key:
            raise ValueError(
                "Watsonx API key is required. "
                "Set WATSONX_API_KEY environment variable or configure in settings."
            )
        if not project_id:
            raise ValueError(
                "Watsonx project ID is required. "
                "Set WATSONX_PROJECT_ID environment variable or configure in settings."
            )

        # CRITICAL: Set project ID as environment variable (required by watsonx.ai SDK)
        os.environ["WATSONX_PROJECT_ID"] = project_id

        # CRITICAL: Also set the base URL as WATSONX_URL (some integrations use this)
        os.environ["WATSONX_URL"] = base_url

        # Ensure model has provider prefix for CrewAI (watsonx/provider/model)
        # Format: watsonx/ibm/granite-3-8b-instruct
        if not model.startswith("watsonx/"):
            model = f"watsonx/{model}"

        logger.info(f"Using WatsonX model: {model}")

        # Create LLM with project_id parameter (CRITICAL!)
        return LLM(
            model=model,
            api_key=api_key,
            base_url=base_url,
            project_id=project_id,  # ← CRITICAL: This is required for WatsonX!
            temperature=settings.watsonx.temperature,
            max_tokens=settings.watsonx.max_tokens,
        )

    if provider == LLMProvider.ollama:
        # Use settings config if available, otherwise fall back to env vars
        model = settings.ollama.model or os.getenv("CFO_OLLAMA_MODEL", "llama3")
        base_url = settings.ollama.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Validate required configuration
        if not base_url:
            raise ValueError(
                "Ollama base URL is required. "
                "Set OLLAMA_BASE_URL environment variable or configure in settings."
            )

        # Ensure model has provider prefix for CrewAI
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"

        logger.info(f"Using Ollama model: {model} at {base_url}")
        return LLM(
            model=model,
            base_url=base_url,
            temperature=settings.ollama.temperature,
        )

    raise ValueError(f"Unsupported provider: {provider}")


def test_llm_connection() -> bool:
    """
    Test if the current LLM provider is accessible.

    Returns:
        True if connection successful
    """
    try:
        llm = build_llm()
        # Try a simple test prompt
        response = llm.call(["Test connection: respond with 'OK'"])
        logger.info(f"LLM connection test successful: {response}")
        return True
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        return False
