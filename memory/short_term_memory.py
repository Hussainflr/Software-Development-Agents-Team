from database.repository import Repository


class ShortTermMemory:
    """Stores run-scoped summaries that can be reset/archive after the run."""

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def remember(self, run_id: int, key: str, value: str) -> None:
        self.repository.upsert_short_term_memory(run_id, key, self._summarize(value))

    def recall(self, run_id: int) -> list[dict[str, str]]:
        return [
            {"key": row.key, "value": row.value}
            for row in self.repository.list_short_term_memory(run_id)
        ]

    def _summarize(self, value: str) -> str:
        return value.strip()[:3000]
