import json
from collections import defaultdict
from tavily import TavilyClient
from groq import Groq
from app.models.schemas import SearchResult
from app.core.config import get_settings
from app.core.prompts import QUERY_EXPANSION_SYSTEM_PROMPT, QUERY_EXPANSION_USER_PROMPT


class SearchService:
    def __init__(self):
        self.settings = get_settings()
        self.tavily = TavilyClient(api_key=self.settings.tavily_api_key)
        self.groq = Groq(api_key=self.settings.groq_api_key)

    def expand_query(self, query: str) -> list[str]:
        """Use LLM to generate 3 query variants."""
        try:
            response = self.groq.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": QUERY_EXPANSION_SYSTEM_PROMPT},
                    {"role": "user", "content": QUERY_EXPANSION_USER_PROMPT.format(query=query)}
                ],
                temperature=0.7
            )
            raw = response.choices[0].message.content.strip()
            clean = raw.replace("```json", "").replace("```", "").strip()
            variants = json.loads(clean)
            return variants if isinstance(variants, list) else []
        except Exception:
            return []

    def _tavily_search(self, query: str, max_results: int) -> list[dict]:
        """Run a single Tavily search, return raw results."""
        try:
            response = self.tavily.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            return response.get("results", [])
        except Exception:
            return []

    def _reciprocal_rank_fusion(
        self, result_lists: list[list[dict]], k: int = 60
    ) -> list[dict]:
        """
        Combine multiple ranked result lists using Reciprocal Rank Fusion.
        RRF score = sum(1 / (k + rank)) across all lists.
        """
        scores: dict[str, float] = defaultdict(float)
        docs: dict[str, dict] = {}

        for results in result_lists:
            for rank, item in enumerate(results, start=1):
                url = item.get("url", "")
                if not url:
                    continue
                scores[url] += 1.0 / (k + rank)
                if url not in docs:
                    docs[url] = item

        sorted_urls = sorted(scores.keys(), key=lambda u: scores[u], reverse=True)
        fused = []
        for url in sorted_urls:
            doc = docs[url]
            doc["rrf_score"] = scores[url]
            fused.append(doc)

        return fused

    def search(self, query: str, max_results: int = 5) -> tuple[list[SearchResult], list[str]]:
        """
        Expand query → search all variants → RRF → return top results + variants.
        Returns (results, query_variants).
        """
        variants = self.expand_query(query)
        all_queries = [query] + variants

        result_lists = []
        for q in all_queries:
            results = self._tavily_search(q, max_results=max_results)
            result_lists.append(results)

        fused = self._reciprocal_rank_fusion(result_lists)[:max_results]

        search_results = []
        for item in fused:
            search_results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    relevance_score=item.get("rrf_score", item.get("score", 0.0))
                )
            )

        return search_results, variants


def get_search_service() -> SearchService:
    return SearchService()
