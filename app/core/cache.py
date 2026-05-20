import threading
import time
from typing import Any


class LocalCache:
    def __init__(self, cleanup_interval: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._start_cleanup()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at is not None and time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        expires_at = time.monotonic() + ttl if ttl else None
        with self._lock:
            self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def clear_user_session(self, user_id: int) -> None:
        prefix = f'user:{user_id}:'
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]

    def clear_all(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)

    def _cleanup_expired(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
            for k in expired:
                del self._store[k]

    def _start_cleanup(self) -> None:
        def run():
            while True:
                time.sleep(self._cleanup_interval)
                self._cleanup_expired()

        t = threading.Thread(target=run, daemon=True)
        t.start()


cache = LocalCache()
