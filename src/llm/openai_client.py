import os
from typing import List, Optional, Dict, Any

from openai import AsyncOpenAI

from .client import LLMClient, LLMMessage, LLMResponse


class OpenAIClient(LLMClient):
    """Direct OpenAI Chat Completions client used by the agent loop."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.model = model
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key must be provided or set in OPENAI_API_KEY env var"
            )
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)

    @staticmethod
    def _to_openai_messages(messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for msg in messages:
            entry: Dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            if msg.role == "tool":
                if msg.tool_call_id:
                    entry["tool_call_id"] = msg.tool_call_id
                if msg.name:
                    entry["name"] = msg.name
            formatted.append(entry)
        return formatted

    @staticmethod
    def _serialize_tool_calls(tool_calls) -> Optional[List[Dict[str, Any]]]:
        if not tool_calls:
            return None
        return [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._to_openai_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content,
            finish_reason=choice.finish_reason or "stop",
            usage={
                "promptTokens": usage.prompt_tokens if usage else 0,
                "completionTokens": usage.completion_tokens if usage else 0,
                "totalTokens": usage.total_tokens if usage else 0,
            },
        )

    async def generate_with_tools(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._to_openai_messages(messages),
            tools=tools or None,
            tool_choice="auto" if tools else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content,
            tool_calls=self._serialize_tool_calls(choice.message.tool_calls),
            finish_reason=choice.finish_reason or "stop",
            usage={
                "promptTokens": usage.prompt_tokens if usage else 0,
                "completionTokens": usage.completion_tokens if usage else 0,
                "totalTokens": usage.total_tokens if usage else 0,
            },
        )
