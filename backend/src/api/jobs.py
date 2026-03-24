import threading
import uuid
from datetime import datetime, timezone

_lock = threading.Lock()
_jobs: dict[str, dict] = {}


def create_job() -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    return job_id


def update_job(job_id: str, status: str, result=None, error=None):
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = status
            _jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            if result is not None:
                _jobs[job_id]["result"] = result
            if error is not None:
                _jobs[job_id]["error"] = error


def get_job(job_id: str) -> dict | None:
    with _lock:
        return _jobs.get(job_id, {}).copy() if job_id in _jobs else None


def clear_all():
    """For test cleanup only."""
    with _lock:
        _jobs.clear()
