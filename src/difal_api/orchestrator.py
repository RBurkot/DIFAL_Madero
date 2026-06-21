import shutil
from pathlib import Path

from difal_apuracao.calculator import calcular_apuracao
from difal_apuracao.config import load_config as load_apuracao_config
from difal_apuracao.reader import read_bi
from difal_apuracao.writer import write_difal_sheet
from difal_importacao.config import load_config as load_importacao_config
from difal_importacao.reader import load_sft_lookups, read_difal
from difal_importacao.reconciliation import reconciliar, save_relatorio
from difal_importacao.transformer import gerar_lancamentos
from difal_importacao.writer import write_importacao_sheet

from difal_api.job_store import clear_active_lock, jobs_dir, save_job


STEPS = [
    ("validacao", "Validação de arquivos"),
    ("apuracao_difal", "Apuração DIFAL"),
    ("importacao", "INDUSTRIA-IMPORTAÇÃO"),
    ("reconciliacao", "Reconciliação"),
]


def _update_step(job: dict, step_id: str, status: str, progress: int = 0, message: str = "") -> None:
    for s in job["steps"]:
        if s["id"] == step_id:
            s["status"] = status
            s["progress_pct"] = progress
            if message:
                s["message"] = message
    save_job(job["id"], job)


def run_job(job_id: str, referencia: Path | None = None) -> None:
    job = __import__("difal_api.job_store", fromlist=["load_job"]).load_job(job_id)
    job_dir = jobs_dir() / job_id
    output_dir = job_dir / "output"

    try:
        _update_step(job, "validacao", "running", 50)
        periodo = job["periodo"].replace("/", ".")
        mes, ano = periodo.split(".")
        cfg_a = load_apuracao_config()
        cfg_i = load_importacao_config()
        workbook_out = output_dir / f"resultado-{periodo.replace('.', '')}.xlsx"

        bi_path = Path(job["uploads"]["bi"]) if job.get("uploads", {}).get("bi") else None
        difal_path = Path(job["uploads"]["difal"]) if job.get("uploads", {}).get("difal") else None

        mode = job["mode"]
        _update_step(job, "validacao", "completed", 100)

        if mode in ("completo", "somente_apuracao") and bi_path:
            _update_step(job, "apuracao_difal", "running", 10)
            linhas_bi = read_bi(bi_path, int(mes), int(ano), job.get("corte_dia"))
            linhas_difal = calcular_apuracao(linhas_bi, cfg_a)
            write_difal_sheet(linhas_difal, workbook_out, periodo)
            job["metrics"] = {"linhas_apuradas": len(linhas_difal)}
            _update_step(job, "apuracao_difal", "completed", 100, f"{len(linhas_difal)} linhas")
            source_for_import = workbook_out
        elif mode == "somente_importacao" and difal_path:
            _update_step(job, "apuracao_difal", "skipped", 100)
            source_for_import = difal_path
            shutil.copy(difal_path, workbook_out)
        else:
            raise ValueError("Arquivos de entrada incompatíveis com o modo selecionado")

        if mode in ("completo", "somente_importacao"):
            _update_step(job, "importacao", "running", 20)
            periodo_obj, linhas = read_difal(source_for_import)
            lookups = load_sft_lookups(source_for_import, referencia)
            ref_path = str(referencia) if referencia and referencia.exists() else None
            if ref_path:
                cfg_i = cfg_i.model_copy(update={"sb1_workbook": ref_path})
            result = gerar_lancamentos(
                linhas, periodo_obj, cfg_i, lookups,
                sb1_workbook=ref_path,
                entradas_workbook=ref_path or source_for_import,
            )
            enriquecidos = sum(
                1 for l in result.lancamentos if l.nome_fornecedor and l.data_emissao and l.data_entrada
            )
            job["metrics"]["sft_chaves_indexadas"] = len(lookups)
            job["metrics"]["lancamentos_enriquecidos_sft"] = enriquecidos
            write_importacao_sheet(result.lancamentos, result.totais_difal, workbook_out, source_for_import)
            job["metrics"]["lancamentos_gerados"] = len(result.lancamentos)
            _update_step(job, "importacao", "completed", 100)

        if referencia and referencia.exists() and workbook_out.exists():
            _update_step(job, "reconciliacao", "running", 50)
            rel = reconciliar(workbook_out, referencia, cfg_i, periodo)
            rel_path = output_dir / "reconciliacao.json"
            save_relatorio(rel, rel_path)
            job["result"] = {
                "reconciliacao_status": rel.resultado,
                "workbook": str(workbook_out),
                "relatorio": str(rel_path),
                **job.get("metrics", {}),
            }
            _update_step(job, "reconciliacao", "completed", 100, rel.resultado)
        else:
            job["result"] = {"workbook": str(workbook_out), **job.get("metrics", {})}
            _update_step(job, "reconciliacao", "skipped", 100, "Sem referência")

        job["status"] = "completed"
        save_job(job_id, job)
    except Exception as e:
        job["status"] = "failed"
        job["error_summary"] = str(e)[:200]
        save_job(job_id, job)
        raise
    finally:
        clear_active_lock()
