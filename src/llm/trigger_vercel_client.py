"""
Trigger.dev Vercel AI SDK v5 Client

Python client that calls Node.js Trigger.dev jobs running Vercel AI SDK v5.
Provides literal compliance with "must use Vercel AI SDK" requirement while
maintaining clean Python agent architecture.
"""

import os
import json
import asyncio
from typing import List, Optional, Dict, Any
import httpx

from .client import LLMClient, LLMMessage, LLMResponse


class TriggerVercelClient(LLMClient):
    """
    LLM client that uses Vercel AI SDK v5 via Trigger.dev Node.js jobs.
    
    Architecture:
    Python Agent → Trigger.dev API → Node.js Job → Vercel AI SDK v5 → OpenAI
    
    This provides:
    - Literal use of Vercel AI SDK (v5+) as required
    - Clean Python architecture
    - No HTTP bridge overhead (Trigger.dev native)
    - Swappable for Sovereign AI CEO
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        api_url: str = "https://api.trigger.dev",
        timeout: float = 120.0,
    ):
        """
        Initialize Trigger Vercel client.
        
        Args:
            model: OpenAI model name (used by Vercel AI SDK)
            api_key: Trigger.dev API key (defaults to TRIGGER_API_KEY env var)
            api_url: Trigger.dev API URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key or os.getenv("TRIGGER_API_KEY")
        self.api_url = api_url
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError(
                "Trigger.dev API key must be provided or set in TRIGGER_API_KEY env var"
            )
        
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.timeout),
        )
    
    async def _trigger_job(
        self,
        task_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger a Trigger.dev job and wait for result.
        
        Args:
            task_id: Trigger.dev task ID
            payload: Job payload
            
        Returns:
            Job result
            
        Raises:
            Exception: If job fails
        """
        try:
            # Trigger the job
            trigger_response = await self.client.post(
                f"/api/v1/tasks/{task_id}/trigger",
                json={"payload": payload}
            )
            trigger_response.raise_for_status()
            run_data = trigger_response.json()
            
            run_id = run_data.get("id")
            
            if not run_id:
                raise ValueError(f"No run ID returned from Trigger.dev. Response: {run_data}")
            
            # Poll for result (with exponential backoff)
            max_attempts = 60
            delay = 1.0
            
            for attempt in range(max_attempts):
                await asyncio.sleep(delay)
                
                try:
                    status_response = await self.client.get(
                        f"/api/v3/runs/{run_id}"
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    status = status_data.get("status")
                    
                    if status == "COMPLETED":
                        return status_data.get("output", {})
                    elif status in ["FAILED", "CANCELED", "CRASHED", "SYSTEM_FAILURE"]:
                        error = status_data.get("error", "Job failed")
                        raise Exception(f"Trigger.dev job failed: {error}")
                    
                    # Job is still running (QUEUED, EXECUTING, etc.)
                    # Exponential backoff (max 10s)
                    delay = min(delay * 1.5, 10.0)
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        # Run not created yet, wait and retry
                        # Use shorter initial delay for 404s
                        delay = min(delay * 1.2, 5.0)
                        continue
                    else:
                        # Other HTTP errors should fail immediately
                        raise
            
            raise TimeoutError(f"Job {run_id} timed out after {max_attempts} attempts")
            
        except httpx.HTTPError as e:
            raise Exception(f"Trigger.dev API error: {e}")
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate text using Vercel AI SDK v5 via Trigger.dev.
        
        Args:
            messages: Conversation history
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response
        """
        # Convert to format expected by Node.js job
        payload = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                }
                for msg in messages
            ],
            "temperature": temperature,
            "maxTokens": max_tokens,
            "model": self.model,
        }
        
        # Call Node.js Vercel AI SDK job
        result = await self._trigger_job("llm-generate", payload)
        
        return LLMResponse(
            content=result.get("content"),
            finish_reason=result.get("finishReason", "stop"),
            usage=result.get("usage"),
        )
    
    async def generate_with_tools(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate text with tool calling using Vercel AI SDK v5.
        
        Args:
            messages: Conversation history
            tools: Tool definitions in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response potentially containing tool calls
        """
        # Convert messages including tool responses
        formatted_messages = []
        for msg in messages:
            msg_dict = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.name:
                msg_dict["name"] = msg.name
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            formatted_messages.append(msg_dict)
        
        payload = {
            "messages": formatted_messages,
            "tools": tools,
            "temperature": temperature,
            "maxTokens": max_tokens,
            "model": self.model,
        }
        
        # Call Node.js Vercel AI SDK job with tools
        result = await self._trigger_job("llm-generate-with-tools", payload)
        
        # Extract usage with defaults (handle None values)
        usage_data = result.get("usage", {}) or {}
        
        return LLMResponse(
            content=result.get("content", ""),
            tool_calls=result.get("toolCalls"),
            finish_reason=result.get("finishReason", "stop"),
            usage={
                "promptTokens": usage_data.get("promptTokens") or 0,
                "completionTokens": usage_data.get("completionTokens") or 0,
                "totalTokens": usage_data.get("totalTokens") or 0,
            },
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

