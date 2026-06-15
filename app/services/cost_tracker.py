import json
import os
from datetime import datetime
from app.models.schemas import CostRecord

COST_LOG_PATH = "cost_log.json"


class CostTracker:
    def __init__(self):
        self.path = COST_LOG_PATH
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump([], f)

    def record(self, query: str, tokens_used: int, cost_usd: float):
        record = CostRecord(
            timestamp=datetime.utcnow().isoformat(),
            query=query,
            tokens_used=tokens_used,
            cost_usd=round(cost_usd, 6)
        )
        records = self.load()
        records.append(record.model_dump())
        with open(self.path, "w") as f:
            json.dump(records, f, indent=2)

    def load(self) -> list[dict]:
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def total_cost(self) -> float:
        return sum(r.get("cost_usd", 0) for r in self.load())

    def total_tokens(self) -> int:
        return sum(r.get("tokens_used", 0) for r in self.load())


def get_cost_tracker() -> CostTracker:
    return CostTracker()
