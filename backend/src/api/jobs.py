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
            "progress": None,
            "log": [],
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


def update_job_progress(job_id: str, progress_data: dict):
    """Update progress field. progress_data: {"step": str, "detail": str}"""
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["progress"] = progress_data
            _jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()


def append_job_log(job_id: str, entry: dict):
    """Append a log entry. entry: {step, case_id, case_index, total, detail, type}"""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["log"].append(entry)


def get_job_log(job_id: str, since: int = 0) -> list[dict] | None:
    """Get log entries starting from index `since`. Returns None if job not found."""
    with _lock:
        if job_id not in _jobs:
            return None
        return _jobs[job_id]["log"][since:]


def get_job(job_id: str) -> dict | None:
    with _lock:
        if job_id not in _jobs:
            return None
        job = _jobs[job_id].copy()
        job.pop("log", None)  # Don't include log in status polling
        return job


def clear_all():
    """For test cleanup only."""
    with _lock:
        _jobs.clear()
