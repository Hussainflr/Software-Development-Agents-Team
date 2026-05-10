from database.repository import Repository


class LongTermMemory:
    """Stores reusable summaries only, designed to be replaced by RAG later."""

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def remember(self, category: str, summary: str, source_run_id: int | None = None) -> None:
        cleaned = self._sanitize(summary)
        if cleaned:
            self.repository.add_long_term_memory(category, cleaned, source_run_id=source_run_id)

    def retrieve(self, query: str, limit: int = 5) -> list[str]:
        return [row.summary for row in self.repository.search_long_term_memory(query, limit=limit)]

    def _sanitize(self, summary: str) -> str:
        blocked = ("API_KEY", "SECRET", "TOKEN", "PASSWORD")
        cleaned = summary.strip()[:2000]
        if any(marker in cleaned.upper() for marker in blocked):
            return ""
        return cleaned
