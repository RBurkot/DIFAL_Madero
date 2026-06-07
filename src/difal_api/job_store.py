import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _data_root() -> Path:
    env = os.environ.get("DIFAL_DATA_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data"


def jobs_dir() -> Path:
    d = _data_root() / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def uploads_dir() -> Path:
    d = _data_root() / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def active_lock() -> Path:
    return _data_root() / "active_job.lock"


def create_job(data: dict) -> str:
    if active_lock().exists():
        raise RuntimeError("Outro processamento em andamento")
    job_id = str(uuid.uuid4())
    job_dir = jobs_dir() / job_id
    job_dir.mkdir(parents=True)
    (job_dir / "output").mkdir()
    data["id"] = job_id
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    save_job(job_id, data)
    active_lock().write_text(job_id, encoding="utf-8")
    return job_id


def save_job(job_id: str, data: dict) -> None:
    path = jobs_dir() / job_id / "job.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load_job(job_id: str) -> dict:
    path = jobs_dir() / job_id / "job.json"
    return json.loads(path.read_text(encoding="utf-8"))


def clear_active_lock() -> None:
    if active_lock().exists():
        active_lock().unlink()


def list_jobs(limit: int = 10) -> list[dict]:
    items = []
    for p in sorted(jobs_dir().iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_dir() and (p / "job.json").exists():
            items.append(load_job(p.name))
            if len(items) >= limit:
                break
    return items
