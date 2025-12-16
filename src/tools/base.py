"""Base tool abstract class"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.
    
    Tools are the primary way for the agent to interact with external
    systems and perform actions.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for the tool (used by LLM to call it)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """
        JSON Schema defining the parameters this tool accepts.
        
        Should follow OpenAI function calling format:
        {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string",
                    "description": "..."
                }
            },
            "required": ["param_name"]
        }
        """
        pass

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Dictionary of parameters matching the schema
            
        Returns:
            Dictionary containing the result of execution
            
        Raises:
            ValueError: If parameters are invalid
            Exception: If tool execution fails
        """
        pass

    def to_openai_format(self) -> Dict[str, Any]:
        """
        Convert tool definition to OpenAI function calling format.
        
        Returns:
            Dictionary in OpenAI tools format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

