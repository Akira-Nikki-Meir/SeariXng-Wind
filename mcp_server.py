"""
SearXNG MCP Server — wraps the SearXNG search API as MCP tools.

Usage:
    python mcp_server.py                        # SSE transport (default)
    python mcp_server.py --transport stdio      # stdio transport (Claude Code)
    python mcp_server.py --url http://localhost:8888  # custom SearXNG URL

Requires: SearXNG running at the configured URL.
"""

import argparse
import sys
from mcp.server.fastmcp import FastMCP

# ─── Config ──────────────────────────────────────────────────────────────────
DEFAULT_URL = "http://127.0.0.1:8888"
TIMEOUT = 15  # seconds

# Category mapping: SearXNG category names → readable descriptions
CATEGORIES = {
    "general": "General web search (Google, DuckDuckGo, Wikipedia, etc.)",
    "it": "Information technology (GitHub, PyPI, MDN, Docker Hub, etc.)",
    "science": "Academic and scientific (arXiv, Semantic Scholar, etc.)",
    "news": "News sources",
    "images": "Image search",
    "videos": "Video search (YouTube, Dailymotion, Piped, etc.)",
    "music": "Music search",
    "files": "File search",
    "maps": "Map search (OpenStreetMap)",
    "social media": "Social media (Lemmy, Mastodon, etc.)",
}

# ─── Server ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="SearXNG MCP Server")
parser.add_argument(
    "--url", default=DEFAULT_URL,
    help=f"SearXNG URL (default: {DEFAULT_URL})"
)
parser.add_argument(
    "--transport", default="sse", choices=["sse", "stdio"],
    help="Transport mode (default: sse)"
)
args = parser.parse_args()

mcp = FastMCP(
    "searxng-search",
    instructions="Search the web via a self-hosted SearXNG instance. Use search() for general queries, or use the category-specific tools (search_images, search_videos, search_its, etc.).",
)

# ─── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def search(
    query: str,
    categories: str = "",
    language: str = "all",
    time_range: str = "",
    safe_search: str = "0",
    page: int = 1,
    engines: str = "",
    max_results: int = 10,
) -> dict:
    """Search the web via SearXNG.

    Args:
        query: The search query string.
        categories: Comma-separated SearXNG categories.
            Options: general, it, science, news, images, videos, music, files, maps, social media.
            Empty = search all categories.
        language: BCP-47 language tag (e.g. 'en', 'de', 'ja', 'zh'). 'all' = auto-detect.
        time_range: Time filter: 'day', 'week', 'month', 'year'. Empty = any time.
        safe_search: '0' = none, '1' = moderate, '2' = strict.
        page: Result page number (1-based).
        engines: Comma-separated engine names to use. Empty = use all enabled engines.
            Common: google, duckduckgo, wikipedia, brave, bing, youtube, github.
        max_results: Maximum number of results to return (1–100).
    """
    import httpx

    params = {
        "q": query,
        "format": "json",
        "pageno": page,
    }

    if categories:
        params["categories"] = categories
    if language and language != "all":
        params["language"] = language
    if time_range:
        params["time_range"] = time_range
    if safe_search in ("0", "1", "2"):
        params["safesearch"] = safe_search
    if engines:
        params["engines"] = engines

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(f"{args.url}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return {
            "error": f"SearXNG connection failed: {e}",
            "suggestion": "Make sure SearXNG is running at the configured URL.",
        }

    results = data.get("results", [])
    total = data.get("number_of_results", 0)

    # Limit results
    results = results[:max_results]

    return {
        "query": query,
        "total_results": total,
        "page": page,
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "engine": r.get("engine", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0),
                "template": r.get("template", ""),
            }
            for r in results
        ],
        "engines_used": list(data.get("engines", [])),
        "search_time": data.get("results_time", 0),
    }


@mcp.tool()
def search_quick(query: str, max_results: int = 5) -> dict:
    """Quick web search with sensible defaults.

    Args:
        query: The search query.
        max_results: Number of results to return (default 5).
    """
    return search(
        query=query,
        categories="general",
        page=1,
        engines="",
        max_results=max_results,
    )


@mcp.tool()
def search_images(query: str, max_results: int = 10) -> dict:
    """Search for images via SearXNG.

    Args:
        query: The search query.
        max_results: Number of image results to return (default 10).
    """
    return search(
        query=query,
        categories="images",
        page=1,
        engines="",
        max_results=max_results,
    )


@mcp.tool()
def search_videos(query: str, max_results: int = 10) -> dict:
    """Search for videos via SearXNG.

    Args:
        query: The search query.
        max_results: Number of video results to return (default 10).
    """
    return search(
        query=query,
        categories="videos",
        page=1,
        engines="",
        max_results=max_results,
    )


@mcp.tool()
def search_its(query: str, max_results: int = 10) -> dict:
    """Search for IT/developer resources via SearXNG.

    Args:
        query: The search query.
        max_results: Number of results to return (default 10).
    """
    return search(
        query=query,
        categories="it",
        page=1,
        engines="",
        max_results=max_results,
    )


@mcp.tool()
def search_academic(query: str, max_results: int = 10) -> dict:
    """Search academic and scientific resources via SearXNG.

    Args:
        query: The search query.
        max_results: Number of results to return (default 10).
    """
    return search(
        query=query,
        categories="science",
        page=1,
        engines="",
        max_results=max_results,
    )


@mcp.tool()
def search_engine(query: str, engine: str, max_results: int = 10) -> dict:
    """Search using a single specific SearXNG engine.

    Args:
        query: The search query.
        engine: Single engine name (e.g. 'google', 'duckduckgo', 'wikipedia', 'github', 'youtube').
        max_results: Number of results to return (default 10).
    """
    return search(
        query=query,
        categories="general",
        page=1,
        engines=engine,
        max_results=max_results,
    )


@mcp.tool()
def list_engines() -> dict:
    """List all available SearXNG search engines and their categories.

    Use this to discover which engines you can query directly.
    """
    import httpx

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Query multiple categories to hit different engines
            all_engines = set()
            categories_to_query = [
                {"q": "python programming", "categories": "general,it,science"},
                {"q": "cat", "categories": "images"},
                {"q": "music", "categories": "videos,music"},
                {"q": "map", "categories": "maps"},
            ]
            for cat_params in categories_to_query:
                try:
                    resp = client.get(f"{args.url}/search", params={**cat_params, "format": "json"})
                    data = resp.json()
                    for r in data.get("results", []):
                        e = r.get("engine", "")
                        if e:
                            all_engines.add(e)
                except Exception:
                    pass
    except httpx.HTTPError as e:
        return {
            "error": f"SearXNG connection failed: {e}",
            "suggestion": "Make sure SearXNG is running at the configured URL.",
        }

    return {
        "engines": sorted(all_engines),
        "category_map": CATEGORIES,
        "note": "To use a specific engine, pass its name to the search tool as 'engines' parameter.",
    }


@mcp.tool()
def search_with_time(query: str, time_range: str, max_results: int = 10) -> dict:
    """Search with a time-based filter.

    Args:
        query: The search query.
        time_range: Time filter — 'day', 'week', 'month', or 'year'.
        max_results: Number of results to return (default 10).
    """
    return search(
        query=query,
        categories="general",
        time_range=time_range,
        page=1,
        engines="",
        max_results=max_results,
    )


@mcp.tool()
def search_multilang(query: str, language: str, max_results: int = 10) -> dict:
    """Search in a specific language.

    Args:
        query: The search query.
        language: BCP-47 language tag (e.g. 'en', 'de', 'ja', 'zh', 'es', 'fr', 'ru').
        max_results: Number of results to return (default 10).
    """
    return search(
        query=query,
        categories="general",
        language=language,
        page=1,
        engines="",
        max_results=max_results,
    )


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport=args.transport)
