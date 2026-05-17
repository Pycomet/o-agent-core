"""Tool registry for managing and discovering available tools"""

from typing import Dict, List, Optional, Any

from .base import BaseTool
from .math_tool import MathTool


class ToolRegistry:
    """
    Registry for managing available tools.

    Handles tool discovery, schema conversion, and routing execution
    calls to the correct tool instances.
    """

    def __init__(self, tools: Optional[List[BaseTool]] = None):
        """
        Initialize the tool registry.

        Args:
            tools: Optional list of tool instances. If None, registers
                   the built-in starter tools (MathTool).
        """
        if tools is None:
            tools = [MathTool()]

        self._tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self, filter_names: Optional[List[str]] = None) -> List[BaseTool]:
        """
        List available tools.

        Args:
            filter_names: Optional list of tool names to filter to

        Returns:
            List of tool instances
        """
        if filter_names is None:
            return list(self._tools.values())

        return [tool for name, tool in self._tools.items() if name in filter_names]

    def get_tool_definitions(
        self, filter_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tool definitions in OpenAI function calling format.

        Args:
            filter_names: Optional list of tool names to include

        Returns:
            List of tool definitions for LLM
        """
        tools = self.list_tools(filter_names)
        return [tool.to_openai_format() for tool in tools]

    async def execute_tool(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool by name with given parameters.

        Args:
            tool_name: Name of the tool to execute
            params: Parameters to pass to the tool

        Returns:
            Result from tool execution

        Raises:
            ValueError: If tool not found or parameters invalid
            Exception: If tool execution fails
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")

        try:
            return await tool.execute(params)
        except Exception as e:
            # Re-raise with context
            raise Exception(f"Tool '{tool_name}' execution failed: {e}") from e

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a new tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False
