"""Tool definition schemas"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Schema for tool definitions passed to LLM"""

    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(
        ..., description="JSON Schema for tool parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        }
                    },
                    "required": ["query"],
                },
            }
        }
