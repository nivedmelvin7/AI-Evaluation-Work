from typing import Dict, Any, Optional
import threading


class JobStore:
    """
    Thread-safe in-memory job store.
    For production, replace _store and _results with a Redis client.
    """

    def __init__(self):
        self._store: Dict[str, Dict] = {}
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str, **kwargs):
        with self._lock:
            self._store[job_id] = {"job_id": job_id, **kwargs}

    def update(self, job_id: str, **kwargs):
        with self._lock:
            if job_id in self._store:
                self._store[job_id].update(kwargs)

    def get(self, job_id: str) -> Optional[Dict]:
        return self._store.get(job_id)

    def set_result(self, job_id: str, result: Any):
        with self._lock:
            self._results[job_id] = result
            self._store[job_id]["status"] = "complete"

    def get_result(self, job_id: str) -> Optional[Any]:
        return self._results.get(job_id)


job_store = JobStore()
