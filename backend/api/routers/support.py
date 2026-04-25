"""
EmuFlow - AI Support API Router
FastAPI endpoints for the AI customer support agent.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.ai_support.knowledge_base import (
    EMULATOR_FAQS,
    HOTKEY_HELP,
    KnowledgeBase,
)
from services.ai_support.support_agent import EmuFlowSupportAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/support", tags=["support"])

# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_agent() -> EmuFlowSupportAgent:
    """Create and cache the support agent (singleton per process)."""
    return EmuFlowSupportAgent()


@lru_cache(maxsize=1)
def _get_kb() -> KnowledgeBase:
    return KnowledgeBase()


def get_agent() -> EmuFlowSupportAgent:
    return _get_agent()


def get_kb() -> KnowledgeBase:
    return _get_kb()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    device_context: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional device metadata: device_name, android_version, "
            "installed_emulators (list), storage_gb."
        ),
    )


class ChatResponse(BaseModel):
    reply: str
    classified_category: str | None = None


class ClassifyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ClassifyResponse(BaseModel):
    category: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/chat",
    summary="Send a message to the EmuFlow AI support agent.",
    response_model=ChatResponse,
)
async def chat(
    body: ChatRequest,
    agent: EmuFlowSupportAgent = Depends(get_agent),
) -> ChatResponse:
    """Submit a support question and receive an AI-generated response.

    The ``conversation_history`` list should contain previous exchanges in
    chronological order so the agent can maintain context.
    """
    history = [{"role": m.role, "content": m.content} for m in body.conversation_history]

    try:
        reply = await agent.chat(
            user_message=body.message,
            conversation_history=history,
            device_context=body.device_context,
        )
    except Exception as exc:
        logger.exception("Support agent chat error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"AI service temporarily unavailable: {exc}",
        ) from exc

    # Silently classify the message for analytics; don't block on failure.
    category: str | None = None
    try:
        category = await agent.classify_issue(body.message)
    except Exception:  # noqa: BLE001
        pass

    return ChatResponse(reply=reply, classified_category=category)


@router.get(
    "/faq",
    summary="Return all frequently asked questions.",
)
async def get_faq() -> dict[str, list[dict[str, str]]]:
    """Return the complete FAQ dictionary grouped by emulator."""
    return EMULATOR_FAQS


@router.get(
    "/faq/{category}",
    summary="Return FAQs for a specific emulator / category.",
)
async def get_faq_by_category(category: str) -> list[dict[str, str]]:
    """Return FAQ entries for *category* (e.g. ``retroarch``, ``ppsspp``,
    ``dolphin``, ``nethersx2``, ``lime3ds``).
    """
    category = category.lower()
    if category not in EMULATOR_FAQS:
        available = sorted(EMULATOR_FAQS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"No FAQs found for category '{category}'. "
            f"Available categories: {available}",
        )
    return EMULATOR_FAQS[category]


@router.post(
    "/classify",
    summary="Classify a support message into a category.",
    response_model=ClassifyResponse,
)
async def classify_issue(
    body: ClassifyRequest,
    agent: EmuFlowSupportAgent = Depends(get_agent),
) -> ClassifyResponse:
    """Classify *message* into one of:
    ``installation``, ``controls``, ``bios``, ``hardware``,
    ``frontend``, ``update``, ``other``.
    """
    try:
        category = await agent.classify_issue(body.message)
    except Exception as exc:
        logger.exception("Classification error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Classification service unavailable: {exc}",
        ) from exc
    return ClassifyResponse(category=category)


@router.get(
    "/hotkeys/{emulator}",
    summary="Return hotkey bindings for a specific emulator / standard.",
)
async def get_hotkeys(emulator: str) -> dict[str, Any]:
    """Return the hotkey help for *emulator*.

    Valid values: ``retroarch_rgc``, ``retroarch_techdweeb``,
    ``ppsspp``, ``dolphin``.
    """
    emulator = emulator.lower()
    if emulator not in HOTKEY_HELP:
        available = sorted(HOTKEY_HELP.keys())
        raise HTTPException(
            status_code=404,
            detail=f"No hotkey data for '{emulator}'. "
            f"Available: {available}",
        )
    return HOTKEY_HELP[emulator]


@router.get(
    "/search",
    summary="Search the EmuFlow knowledge base.",
)
async def knowledge_search(
    query: str,
    kb: KnowledgeBase = Depends(get_kb),
) -> dict[str, Any]:
    """Perform a keyword search over the built-in knowledge base.

    Returns up to 5 relevant snippets.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    results = kb.search(query)
    return {"query": query, "results": results, "count": len(results)}
