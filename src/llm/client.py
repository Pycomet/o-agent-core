from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Message in LLM conversation"""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None  # Tool function name on tool responses
    tool_call_id: Optional[str] = None  # Required by OpenAI on tool responses
    tool_calls: Optional[
        List[Dict[str, Any]]
    ] = None  # For assistant messages with tool calls


class LLMResponse(BaseModel):
    """Response from LLM"""

    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str  # "stop", "tool_calls", "length", etc.
    usage: Optional[Dict[str, int]] = None


class LLMClient(ABC):
    """
    Abstract LLM client interface.

    Designed to match Vercel AI SDK patterns while being swappable
    for future "Sovereign AI CEO" model integration.
    """

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: Conversation history
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a completion with tool calling capability.

        Args:
            messages: Conversation history
            tools: List of tool definitions in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse potentially containing tool calls
        """
        pass
