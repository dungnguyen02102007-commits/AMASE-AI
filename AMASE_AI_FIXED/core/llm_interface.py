"""
core/llm_interface.py
─────────────────────────────────────────────────────────────────
Unified LLM abstraction layer.

Design decisions:
- Both Gemini and Claude expose an identical async interface.
- The calling agent never imports LangChain internals directly.
- Swapping models = changing one config value.
- Tenacity handles transient API failures with exponential backoff.
"""

from __future__ import annotations
import openai
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import Config
from core.logger import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────
# BASE INTERFACE
# ────────────────────────────────────────────────────────────────

class LLMInterface(ABC):
    """
    Abstract base for all LLM backends.
    Enforces a uniform async call signature across providers.
    """

    @abstractmethod
    async def ainvoke(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
    ) -> str:
        """
        Async invoke the LLM with a list of messages.

        Args:
            messages   : List of LangChain BaseMessage objects.
            temperature: Override the default temperature for this call.

        Returns:
            The LLM's text response as a plain string.
        """
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the canonical model identifier string."""
        ...


# ────────────────────────────────────────────────────────────────
# GEMINI IMPLEMENTATION
# ────────────────────────────────────────────────────────────────

class GeminiLLM(LLMInterface):
    """
    Google Gemini wrapper.
    Used by Agent 1 (Data Collection).
    """

    def __init__(
        self,
        model: str = Config.GEMINI_MODEL,
        temperature: float = Config.LLM_TEMPERATURE,
    ) -> None:
        self._model_name = model
        self._default_temperature = temperature
        self._client = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True,
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(min=Config.RETRY_WAIT_SECONDS, max=30),
        retry=retry_if_exception_type(Exception),
    )
    async def ainvoke(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
    ) -> str:
        if temperature is not None:
            client = ChatGoogleGenerativeAI(
                model=self._model_name,
                google_api_key=Config.GOOGLE_API_KEY,
                temperature=temperature,
                convert_system_message_to_human=True,
            )
        else:
            client = self._client

        logger.debug(
            "gemini_invoke",
            model=self._model_name,
            message_count=len(messages),
        )
        response = await client.ainvoke(messages)
        return response.content

    def get_model_name(self) -> str:
        return self._model_name


# ────────────────────────────────────────────────────────────────
# ChatGPT IMPLEMENTATION
# ────────────────────────────────────────────────────────────────

class ChatGPTLLM(LLMInterface):
    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        self.api_key = api_key
        self.model = model
        openai.api_key = self.api_key

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=30),
        retry=retry_if_exception_type(Exception),
    )
    async def ainvoke(self, messages: List):
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message['content']

    def get_model_name(self) -> str:
        return self.model


# ────────────────────────────────────────────────────────────────
# FACTORY
# ────────────────────────────────────────────────────────────────

class LLMFactory:
    """
    Factory for creating LLM instances by provider name.
    Decouples agent code from specific LLM constructors.
    """

    _registry: dict[str, type] = {
        "gemini": GeminiLLM,
        "chatgpt": ChatGPTLLM,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMInterface:
        """
        Create an LLM instance.

        Args:
            provider   : "gemini" or "claude"
            model      : Override default model string.
            temperature: Override default temperature.

        Returns:
            An LLMInterface-compliant instance.
        """
        provider = provider.lower()
        if provider not in cls._registry:
            raise ValueError(
                f"Unknown LLM provider '{provider}'. "
                f"Available: {list(cls._registry.keys())}"
            )

        kwargs: dict = {}
        if model:
            kwargs["model"] = model
        if temperature is not None:
            kwargs["temperature"] = temperature

        return cls._registry[provider](**kwargs)

    @classmethod
    def register(cls, name: str, klass: type) -> None:
        """
        Register a new LLM backend at runtime.
        Supports extensibility without modifying factory code.
        """
        cls._registry[name] = klass
