from tavily import TavilyClient
from app.models.schemas import SearchResult
from app.core.config import get_settings


class SearchService:
    def __init__(self):
        self.settings = get_settings()
        self.client = TavilyClient(api_key=self.settings.tavily_api_key)

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )

        results = []
        for item in response.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    relevance_score=item.get("score", 0.0)
                )
            )

        return results


def get_search_service() -> SearchService:
    return SearchService()