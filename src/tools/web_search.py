"""Web search tool (mock implementation)"""

from typing import Dict, Any, List
import hashlib

from .base import BaseTool


class WebSearchTool(BaseTool):
    """
    Tool for searching the web.
    
    Currently uses a mock implementation with realistic result structure.
    Can be swapped for real API (Tavily, Serper, etc.) by changing execute().
    """

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for information on any topic. Returns a list of relevant search results with titles, snippets, and URLs."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'Python best practices 2024')",
                }
            },
            "required": ["query"],
        }

    def _generate_mock_results(self, query: str) -> List[Dict[str, str]]:
        """
        Generate mock search results based on query.
        
        In production, this would call a real search API.
        """
        # Use query hash to generate consistent but varied results
        query_hash = int(hashlib.md5(query.encode()).hexdigest(), 16)
        num_results = 3 + (query_hash % 3)  # 3-5 results
        
        results = []
        for i in range(num_results):
            result_num = (query_hash + i) % 10 + 1
            results.append({
                "title": f"Result {result_num}: {query}",
                "snippet": f"This is a relevant snippet about '{query}'. "
                          f"It contains useful information related to your search query. "
                          f"Result quality score: {90 - i * 5}/100.",
                "url": f"https://example.com/article-{result_num}-{query_hash % 1000}",
            })
        
        return results

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            params: Must contain 'query' key with search string
            
        Returns:
            Dictionary with 'results' key containing list of search results
        """
        query = params.get("query")
        if not query:
            raise ValueError("Missing required parameter: query")

        if not isinstance(query, str):
            raise ValueError("Query must be a string")

        if len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")

        # Generate mock results (replace with real API call in production)
        results = self._generate_mock_results(query.strip())
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

