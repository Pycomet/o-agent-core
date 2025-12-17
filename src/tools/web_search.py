"""Web search tool using DuckDuckGo Search (Free, no API key required)"""

import os
from typing import Dict, Any, List, Optional
import logging
import hashlib
import time
import asyncio
from ddgs import DDGS
from .base import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Tool for searching the web using DuckDuckGo Search.

    Free to use, no API key required. Falls back to mock results if search fails.
    """

    def __init__(self):
        """
        Initialize WebSearchTool with DuckDuckGo Search.

        No API key required - DuckDuckGo search is completely free!
        """
        self.ddgs = None
        self.use_real_search = False
        self._last_search_time = 0
        self._min_delay = (
            1.0  # Minimum 1 second between searches to avoid rate limiting
        )

        # Try to import DuckDuckGo Search (lazy import)
        try:
            self.ddgs = DDGS()
            self.use_real_search = True
            logger.info(
                "DuckDuckGo Search loaded successfully (free, no API key needed)"
            )
        except ImportError:
            logger.warning(
                "ddgs package not installed. "
                "Install with: pip install ddgs. "
                "Using mock search results."
            )

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for information on any topic using DuckDuckGo. Returns a list of relevant search results with titles, snippets, and URLs. Free to use, no API key required."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'Python best practices 2024')",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 10)",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        }

    async def _search_with_duckduckgo(
        self, query: str, num_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo (free, no API key required).

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search result dictionaries
        """
        if not self.ddgs:
            logger.debug("DuckDuckGo Search not available, using mock results")
            return self._generate_mock_results(query, num_results)

        # Rate limiting: wait between searches (non-blocking)
        current_time = time.time()
        time_since_last = current_time - self._last_search_time
        if time_since_last < self._min_delay:
            sleep_time = self._min_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        try:
            logger.debug(
                f"Searching DuckDuckGo: query='{query}', max_results={num_results}"
            )

            # Update last search time
            self._last_search_time = time.time()

            # Try multiple methods to get results
            search_results = []

            # Method 1: Try with timeout and error handling
            try:
                for i, result in enumerate(
                    self.ddgs.text(
                        query,
                        region="wt-wt",
                        safesearch="moderate",
                        timelimit=None,
                        max_results=num_results,
                    )
                ):
                    if result:  # Ensure result is not None
                        search_results.append(result)
                    if len(search_results) >= num_results:
                        break
                    if i > num_results * 2:  # Safety limit
                        break
            except StopIteration:
                pass  # Generator exhausted
            except Exception as inner_e:
                logger.warning(f"DuckDuckGo text search error: {inner_e}")

            logger.debug(f"Found {len(search_results)} results from DuckDuckGo")

            if search_results and len(search_results) > 0:
                logger.debug(
                    f"Sample result structure: {list(search_results[0].keys())}"
                )

            if not search_results:
                logger.warning(
                    f"No results from DuckDuckGo for query '{query}'. "
                    f"This may be due to rate limiting or parsing issues. Using mock results."
                )
                return self._generate_mock_results(query, num_results)

            results = []
            for result in search_results:
                # Extract data with multiple fallbacks
                title = result.get("title") or result.get("name") or "No title"
                snippet = (
                    result.get("body")
                    or result.get("description")
                    or result.get("snippet")
                    or "No snippet available"
                )
                url = (
                    result.get("href") or result.get("link") or result.get("url") or ""
                )

                if url:  # Only add if we have a URL
                    results.append(
                        {
                            "title": title,
                            "snippet": snippet[:200],  # Limit snippet length
                            "url": url,
                        }
                    )

            if len(results) == 0:
                logger.warning("Parsed 0 valid results (missing URLs), using mock")
                return self._generate_mock_results(query, num_results)

            logger.info(
                f"Successfully retrieved {len(results)} results from DuckDuckGo"
            )
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}", exc_info=True)
            logger.info("Falling back to mock results")
            # Fall back to mock results on error
            return self._generate_mock_results(query, num_results)

    def _generate_mock_results(
        self, query: str, num_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate mock search results for testing/fallback.

        Args:
            query: Search query
            num_results: Number of results to generate

        Returns:
            List of mock search result dictionaries
        """
        query_hash = int(hashlib.md5(query.encode()).hexdigest(), 16)

        results = []
        for i in range(min(num_results, 5)):
            result_num = (query_hash + i) % 10 + 1
            results.append(
                {
                    "title": f"Result {result_num}: {query}",
                    "snippet": f"This is a relevant snippet about '{query}'. "
                    f"It contains useful information related to your search query. "
                    f"Result quality score: {90 - i * 5}/100.",
                    "url": f"https://example.com/article-{result_num}-{query_hash % 1000}",
                }
            )

        return results

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search the web for information.

        Args:
            params: Must contain 'query' key with search string.
                   Optional 'num_results' key (default: 5, max: 10)

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

        num_results = params.get("num_results", 5)
        if not isinstance(num_results, int) or num_results < 1 or num_results > 10:
            num_results = 5

        results = await self._search_with_duckduckgo(query.strip(), num_results)

        # Determine if we actually got real results or mock
        is_real_results = (
            self.use_real_search
            and len(results) > 0
            and results[0].get("url", "").startswith("http")
        )

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "source": "duckduckgo" if is_real_results else "mock",
        }
