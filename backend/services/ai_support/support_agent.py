"""
EmuFlow - AI Support Agent
Configurable AI customer support for Android retro-emulation.

Provider selection via environment variable:
    SUPPORT_AI_PROVIDER=openai   (default) – uses OpenAI Chat Completions API
    SUPPORT_AI_PROVIDER=ollama            – uses a local Ollama HTTP server
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Je bent EmuFlow Support, een vriendelijke AI-assistent gespecialiseerd in Android retro-emulatie.
Je helpt gebruikers met:
- Installatie en configuratie van emulatoren (RetroArch, PPSSPP, Dolphin, NetherSX2, Lime3DS)
- Controller setup en hotkey configuratie
- BIOS problemen en verificatie
- Hardware compatibiliteitsvragen
- ES-DE en Daijishō frontend setup
- Obtainium update management

Je baseert je antwoorden op de best practices van Retro Game Corps en TechDweeb.
Bij technische problemen vraag je altijd naar: apparaatnaam, Android versie, en de exacte foutmelding.
Je antwoorden zijn bondig (max 3 alinea's), praktisch en vriendelijk.
Antwoord in de taal van de gebruiker."""

# Issue classification categories
ISSUE_CATEGORIES = [
    "installation",
    "controls",
    "bios",
    "hardware",
    "frontend",
    "update",
    "other",
]

CLASSIFICATION_PROMPT = (
    "Classify the following user message into exactly one of these categories: "
    + ", ".join(ISSUE_CATEGORIES)
    + ".\n"
    "Respond with ONLY the category name in lowercase, nothing else.\n\n"
    "User message: {message}"
)

CONFIG_EXPLANATION_PROMPT = (
    "Explain the RetroArch / emulator configuration key '{key}' with value '{value}' "
    "in simple terms for a non-technical Android gaming user. "
    "Keep the explanation under 100 words."
)

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class EmuFlowSupportAgent:
    """AI-powered customer support agent for EmuFlow.

    Supports two backend providers:
    - ``"openai"`` – OpenAI Chat Completions (GPT-4o by default).
    - ``"ollama"`` – Local Ollama server (llama3 by default).

    Configuration via environment variables:

    +----------------------------+------------------------------------------+
    | Variable                   | Description                              |
    +============================+==========================================+
    | ``SUPPORT_AI_PROVIDER``    | ``openai`` or ``ollama`` (default: openai)|
    | ``OPENAI_API_KEY``         | Required for OpenAI provider             |
    | ``OPENAI_MODEL``           | Model name (default: gpt-4o-mini)        |
    | ``OLLAMA_BASE_URL``        | Ollama server URL (default: localhost)   |
    | ``OLLAMA_MODEL``           | Ollama model (default: llama3)           |
    +----------------------------+------------------------------------------+
    """

    def __init__(self) -> None:
        self._provider = os.getenv("SUPPORT_AI_PROVIDER", "openai").lower()
        self._client: Any = None
        self._model: str = ""
        self._init_client()

    # ------------------------------------------------------------------
    # Client initialisation
    # ------------------------------------------------------------------

    def _init_client(self) -> None:
        if self._provider == "openai":
            self._init_openai()
        elif self._provider == "ollama":
            self._init_ollama()
        else:
            raise ValueError(
                f"Unknown SUPPORT_AI_PROVIDER '{self._provider}'. "
                "Must be 'openai' or 'ollama'."
            )

    def _init_openai(self) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is required for SUPPORT_AI_PROVIDER=openai. "
                "Install it with: pip install openai"
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY environment variable is not set."
            )
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info("EmuFlowSupportAgent initialised with OpenAI provider (model: %s).", self._model)

    def _init_ollama(self) -> None:
        """Use OpenAI-compatible Ollama API via the openai client."""
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is required even for Ollama provider. "
                "Install it with: pip install openai"
            ) from exc

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self._client = AsyncOpenAI(api_key="ollama", base_url=base_url)
        self._model = os.getenv("OLLAMA_MODEL", "llama3")
        logger.info("EmuFlowSupportAgent initialised with Ollama provider (model: %s).", self._model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _complete(self, messages: list[dict[str, str]]) -> str:
        """Call the underlying LLM and return the assistant reply."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    def build_context_prompt(self, device_context: dict[str, Any]) -> str:
        """Build a context string from the user's device information.

        Args:
            device_context: Dict with optional keys ``device_name``,
                ``android_version``, ``installed_emulators``, ``storage_gb``.

        Returns:
            A formatted string ready to be appended to the system prompt.
        """
        parts: list[str] = ["--- User Device Context ---"]

        if device_name := device_context.get("device_name"):
            parts.append(f"Device: {device_name}")
        if android_version := device_context.get("android_version"):
            parts.append(f"Android version: {android_version}")
        if emulators := device_context.get("installed_emulators"):
            if isinstance(emulators, list):
                emulators = ", ".join(emulators)
            parts.append(f"Installed emulators: {emulators}")
        if storage := device_context.get("storage_gb"):
            parts.append(f"Available storage: {storage} GB")
        if extra := device_context.get("extra"):
            parts.append(f"Extra info: {extra}")

        parts.append("--- End Context ---")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]],
        device_context: dict[str, Any] | None = None,
    ) -> str:
        """Generate an AI response for the given user message.

        Args:
            user_message: The latest message from the user.
            conversation_history: Previous messages in OpenAI format
                (list of ``{"role": ..., "content": ...}`` dicts).
            device_context: Optional device metadata to inject into the
                system prompt.

        Returns:
            The assistant's reply as a plain string.
        """
        system_content = SYSTEM_PROMPT
        if device_context:
            system_content += "\n\n" + self.build_context_prompt(device_context)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content},
            *conversation_history,
            {"role": "user", "content": user_message},
        ]
        return await self._complete(messages)

    async def classify_issue(self, message: str) -> str:
        """Classify a user message into a predefined support category.

        Args:
            message: Raw user input.

        Returns:
            One of: installation, controls, bios, hardware, frontend,
            update, other.
        """
        prompt = CLASSIFICATION_PROMPT.format(message=message)
        messages = [
            {"role": "system", "content": "You are an expert issue classifier."},
            {"role": "user", "content": prompt},
        ]
        raw = await self._complete(messages)
        category = raw.strip().lower()
        if category not in ISSUE_CATEGORIES:
            logger.warning("Unexpected classification result '%s', defaulting to 'other'.", category)
            return "other"
        return category

    async def generate_config_explanation(
        self, config_key: str, value: str
    ) -> str:
        """Explain a configuration key/value pair in plain language.

        Args:
            config_key: RetroArch or emulator config key name.
            value: Current or proposed value.

        Returns:
            Plain-language explanation (≤ 100 words).
        """
        prompt = CONFIG_EXPLANATION_PROMPT.format(key=config_key, value=value)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return await self._complete(messages)
