import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """Limiteur en mémoire, par clé (adresse IP). Valable pour un seul processus : à remplacer
    par un stockage partagé (ex. PostgreSQL ou Redis) avant de lancer plusieurs instances."""

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        hits = self._hits[key]
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True
