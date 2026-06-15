import json
from groq import Groq
from app.models.schemas import SearchResult
from app.core.config import get_settings
from app.core.prompts import CONFIDENCE_SYSTEM_PROMPT, CONFIDENCE_USER_PROMPT


class ConfidenceService:
    def __init__(self):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.groq_api_key)

    def _build_context(self, sources: list[SearchResult]) -> str:
        return "\n".join([
            f"Source {i}: {source.content[:200]}"
            for i, source in enumerate(sources, 1)
        ])

    def score(self, query: str, answer: str, sources: list[SearchResult]) -> float:
        context = self._build_context(sources)

        response = self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": CONFIDENCE_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": CONFIDENCE_USER_PROMPT.format(
                        query=query,
                        answer=answer,
                        context=context
                    )
                }
            ],
            temperature=0.1
        )

        raw = response.choices[0].message.content
        clean = raw.strip().replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(clean)
            return float(parsed.get("confidence_score", 0.5))
        except Exception:
            return 0.5


def get_confidence_service() -> ConfidenceService:
    return ConfidenceService()