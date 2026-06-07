import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from difal_apuracao.reader import validate_bi_layout
from difal_api import job_store
from difal_api.orchestrator import STEPS, run_job

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "public"
REFERENCIA = next(ROOT.glob("*28*.xlsx"), None)

app = FastAPI(title="DIFAL Indústria Madero", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_events: dict[str, asyncio.Queue] = {}


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "engines": {"apuracao": True, "importacao": True},
        "referencia": str(REFERENCIA) if REFERENCIA else None,
    }


@app.post("/api/v1/uploads")
async def upload(file: UploadFile = File(...), expected_type: str = Form("bi")):
    upload_id = str(uuid.uuid4())
    dest_dir = job_store.uploads_dir() / upload_id
    dest_dir.mkdir(parents=True)
    dest = dest_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    valid, errors = validate_bi_layout(dest) if expected_type == "bi" else (True, [])
    return {
        "id": upload_id,
        "filename": file.filename,
        "path": str(dest),
        "type": expected_type,
        "valid": valid,
        "errors": errors,
        "size_bytes": len(content),
    }


@app.post("/api/v1/jobs")
def create_job(
    background_tasks: BackgroundTasks,
    mode: str = Form("completo"),
    periodo: str = Form(...),
    bi_upload_id: str | None = Form(None),
    difal_upload_id: str | None = Form(None),
    corte_dia: int | None = Form(None),
):
    if job_store.active_lock().exists():
        raise HTTPException(409, "Outro processamento em andamento")

    uploads: dict[str, str] = {}
    if bi_upload_id:
        p = job_store.uploads_dir() / bi_upload_id
        files = list(p.glob("*.xlsx"))
        if files:
            uploads["bi"] = str(files[0])
    if difal_upload_id:
        p = job_store.uploads_dir() / difal_upload_id
        files = list(p.glob("*.xlsx"))
        if files:
            uploads["difal"] = str(files[0])

    job = {
        "mode": mode,
        "periodo": periodo,
        "corte_dia": corte_dia,
        "uploads": uploads,
        "status": "running",
        "steps": [{"id": s[0], "label": s[1], "status": "pending", "progress_pct": 0} for s in STEPS],
        "metrics": {},
    }
    job_id = job_store.create_job(job)
    _events[job_id] = asyncio.Queue()

    def _run():
        try:
            ref = REFERENCIA if REFERENCIA and REFERENCIA.exists() else None
            run_job(job_id, ref)
        except Exception as e:
            j = job_store.load_job(job_id)
            j["status"] = "failed"
            j["error_summary"] = str(e)[:200]
            job_store.save_job(job_id, j)

    background_tasks.add_task(_run)
    return {"id": job_id, "status": "pending", "mode": mode, "periodo": periodo}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str):
    try:
        return job_store.load_job(job_id)
    except FileNotFoundError:
        raise HTTPException(404, "Job não encontrado")


@app.get("/api/v1/jobs")
def list_jobs(limit: int = 10):
    return job_store.list_jobs(limit)


@app.get("/api/v1/jobs/{job_id}/download")
def download(job_id: str):
    job = job_store.load_job(job_id)
    wb = job.get("result", {}).get("workbook")
    if not wb or not Path(wb).exists():
        raise HTTPException(404, "Arquivo não disponível")
    return FileResponse(wb, filename=Path(wb).name)


@app.get("/")
def index():
    index_path = FRONTEND / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>DIFAL Madero API</h1><p>Frontend em frontend/public/index.html</p>")


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
