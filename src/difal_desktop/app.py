"""Interface desktop Tkinter — DIFAL Indústria Madero."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from difal_apuracao.reader import validate_bi_layout
from difal_api import job_store
from difal_api.orchestrator import STEPS, run_job
from difal_desktop.paths import app_root, find_referencia_workbook, setup_runtime

MODES = [
    ("completo", "Completo (BI → DIFAL → Importação)"),
    ("somente_apuracao", "Somente apuração DIFAL"),
    ("somente_importacao", "Somente INDUSTRIA-IMPORTAÇÃO"),
]

STEP_LABELS = {step_id: label for step_id, label in STEPS}


class DifalDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("DIFAL Indústria — Madero")
        self.root.minsize(640, 520)
        self.root.geometry("760x600")

        self.bi_path: Path | None = None
        self.difal_path: Path | None = None
        self.ref_path: Path | None = find_referencia_workbook()
        self.output_dir = app_root() / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.job_id: str | None = None
        self.result_workbook: Path | None = None
        self._poll_after_id: str | None = None
        self._worker: threading.Thread | None = None

        self._build_ui()
        self._refresh_mode_fields()

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 4}
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="DIFAL Indústria — Madero", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            frm,
            text="Geração de planilhas DIFAL e INDUSTRIA-IMPORTAÇÃO",
            foreground="#555",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

        ttk.Label(frm, text="Modo").grid(row=2, column=0, sticky="w", **pad)
        self.mode_var = tk.StringVar(value="completo")
        self.mode_combo = ttk.Combobox(
            frm,
            textvariable=self.mode_var,
            values=[label for _, label in MODES],
            state="readonly",
            width=48,
        )
        self.mode_combo.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_mode_fields())

        ttk.Label(frm, text="Período (MM/AAAA)").grid(row=3, column=0, sticky="w", **pad)
        self.periodo_var = tk.StringVar(value="05/2026")
        ttk.Entry(frm, textvariable=self.periodo_var, width=12).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Corte dia (opcional)").grid(row=4, column=0, sticky="w", **pad)
        self.corte_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.corte_var, width=8).grid(row=4, column=1, sticky="w", **pad)

        self._file_row(frm, 5, "Arquivo BI (.xlsx)", "bi")
        self._file_row(frm, 6, "Arquivo DIFAL (.xlsx)", "difal")
        self._file_row(frm, 7, "Planilha referência (SFT/reconciliação)", "ref", optional=True)

        ttk.Label(frm, text="Pasta de saída").grid(row=8, column=0, sticky="w", **pad)
        self.out_label = ttk.Label(frm, text=str(self.output_dir), wraplength=480)
        self.out_label.grid(row=8, column=1, sticky="w", **pad)
        ttk.Button(frm, text="Escolher…", command=self._pick_output_dir).grid(row=8, column=2, **pad)

        btn_frm = ttk.Frame(frm)
        btn_frm.grid(row=9, column=0, columnspan=3, sticky="w", pady=12)
        self.start_btn = ttk.Button(btn_frm, text="Iniciar processamento", command=self._start)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.open_btn = ttk.Button(btn_frm, text="Abrir planilha gerada", command=self._open_result, state=tk.DISABLED)
        self.open_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.folder_btn = ttk.Button(btn_frm, text="Abrir pasta de saída", command=self._open_output_dir, state=tk.DISABLED)
        self.folder_btn.pack(side=tk.LEFT)

        ttk.Separator(frm).grid(row=10, column=0, columnspan=3, sticky="ew", pady=8)

        ttk.Label(frm, text="Progresso").grid(row=11, column=0, sticky="nw", **pad)
        self.steps_tree = ttk.Treeview(frm, columns=("status", "detail"), show="headings", height=5)
        self.steps_tree.heading("status", text="Etapa")
        self.steps_tree.heading("detail", text="Situação")
        self.steps_tree.column("status", width=220)
        self.steps_tree.column("detail", width=380)
        self.steps_tree.grid(row=11, column=1, columnspan=2, sticky="nsew", **pad)
        for step_id, label in STEPS:
            self.steps_tree.insert("", tk.END, iid=step_id, values=(label, "pendente"))

        ttk.Label(frm, text="Resumo").grid(row=12, column=0, sticky="nw", **pad)
        self.log_text = tk.Text(frm, height=8, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=12, column=1, columnspan=2, sticky="nsew", **pad)
        self.log_text.configure(state=tk.DISABLED)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(12, weight=1)

        self.bi_status = ttk.Label(frm, text="", foreground="#166534")
        self.bi_status.grid(row=5, column=2, sticky="w", **pad)

    def _file_row(self, parent: ttk.Frame, row: int, label: str, kind: str, optional: bool = False) -> None:
        pad = {"padx": 12, "pady": 4}
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", **pad)
        path_label = ttk.Label(parent, text="(não selecionado)" if not optional else "(automático se disponível)", wraplength=420)
        path_label.grid(row=row, column=1, sticky="w", **pad)
        setattr(self, f"{kind}_label", path_label)
        ttk.Button(parent, text="Selecionar…", command=lambda k=kind: self._pick_file(k)).grid(row=row, column=2, **pad)

    def _mode_key(self) -> str:
        label = self.mode_var.get()
        for key, text in MODES:
            if text == label:
                return key
        return "completo"

    def _refresh_mode_fields(self) -> None:
        mode = self._mode_key()
        needs_bi = mode in ("completo", "somente_apuracao")
        needs_difal = mode == "somente_importacao"
        self._set_widget_state(self.bi_label, needs_bi)
        self._set_widget_state(self.difal_label, needs_difal)

    @staticmethod
    def _set_widget_state(label: ttk.Label, active: bool) -> None:
        label.configure(foreground="black" if active else "#999")

    def _pick_file(self, kind: str) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar planilha Excel",
            filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
        )
        if not path:
            return
        p = Path(path)
        if kind == "bi":
            self.bi_path = p
            self.bi_label.configure(text=p.name)
            valid, errors = validate_bi_layout(p)
            if valid:
                self.bi_status.configure(text="✓ Válido", foreground="#166534")
            else:
                self.bi_status.configure(text="✗ " + "; ".join(errors)[:80], foreground="#b91c1c")
        elif kind == "difal":
            self.difal_path = p
            self.difal_label.configure(text=p.name)
        else:
            self.ref_path = p
            self.ref_label.configure(text=p.name)

    def _pick_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Pasta de saída")
        if path:
            self.output_dir = Path(path)
            self.out_label.configure(text=str(self.output_dir))

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _validate_before_start(self) -> str | None:
        mode = self._mode_key()
        periodo = self.periodo_var.get().strip().replace(".", "/")
        if "/" not in periodo:
            return "Informe o período no formato MM/AAAA."
        mes, ano = periodo.split("/")
        if not (mes.isdigit() and ano.isdigit() and 1 <= int(mes) <= 12):
            return "Período inválido."

        if mode in ("completo", "somente_apuracao"):
            if not self.bi_path:
                return "Selecione o arquivo BI."
            valid, errors = validate_bi_layout(self.bi_path)
            if not valid:
                return "Arquivo BI inválido: " + "; ".join(errors)
        if mode == "somente_importacao" and not self.difal_path:
            return "Selecione o arquivo DIFAL."
        if self.corte_var.get().strip():
            if not self.corte_var.get().strip().isdigit():
                return "Corte dia deve ser numérico."
        return None

    def _start(self) -> None:
        err = self._validate_before_start()
        if err:
            messagebox.showerror("Validação", err)
            return
        if job_store.active_lock().exists():
            messagebox.showwarning("Em andamento", "Já existe um processamento em execução.")
            return

        self.start_btn.configure(state=tk.DISABLED)
        self.open_btn.configure(state=tk.DISABLED)
        self.folder_btn.configure(state=tk.DISABLED)
        self.result_workbook = None
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        for step_id, label in STEPS:
            self.steps_tree.item(step_id, values=(label, "pendente"))

        uploads: dict[str, str] = {}
        if self.bi_path:
            uploads["bi"] = str(self.bi_path)
        if self.difal_path:
            uploads["difal"] = str(self.difal_path)

        corte = int(self.corte_var.get()) if self.corte_var.get().strip().isdigit() else None
        job = {
            "mode": self._mode_key(),
            "periodo": self.periodo_var.get().strip(),
            "corte_dia": corte,
            "uploads": uploads,
            "status": "running",
            "steps": [
                {"id": s[0], "label": s[1], "status": "pending", "progress_pct": 0, "message": ""}
                for s in STEPS
            ],
            "metrics": {},
        }
        try:
            self.job_id = job_store.create_job(job)
        except RuntimeError as e:
            messagebox.showerror("Erro", str(e))
            self.start_btn.configure(state=tk.NORMAL)
            return

        referencia = self.ref_path or find_referencia_workbook()
        self._append_log(f"Job {self.job_id[:8]}… iniciado.")

        def _run() -> None:
            try:
                run_job(self.job_id, referencia)
            except Exception:
                pass  # estado failed é lido pelo poll

        self._worker = threading.Thread(target=_run, daemon=True)
        self._worker.start()
        self._poll_job()

    def _poll_job(self) -> None:
        if not self.job_id:
            return
        try:
            job = job_store.load_job(self.job_id)
        except FileNotFoundError:
            return

        for step in job.get("steps", []):
            sid = step["id"]
            if sid in self.steps_tree.get_children():
                detail = f"{step.get('status', '')} {step.get('progress_pct', 0)}%"
                if step.get("message"):
                    detail += f" — {step['message']}"
                self.steps_tree.item(sid, values=(STEP_LABELS.get(sid, sid), detail))

        status = job.get("status")
        if status == "running":
            self._poll_after_id = self.root.after(500, self._poll_job)
            return

        if status == "completed":
            self._on_completed(job)
        elif status == "failed":
            self._on_failed(job.get("error_summary", "Falha desconhecida"))

    def _on_completed(self, job: dict) -> None:
        result = job.get("result", {})
        metrics = job.get("metrics", {})
        wb_src = Path(result.get("workbook", ""))
        if wb_src.exists():
            dest = self.output_dir / wb_src.name
            shutil.copy2(wb_src, dest)
            self.result_workbook = dest
            rel = result.get("relatorio")
            if rel and Path(rel).exists():
                shutil.copy2(rel, self.output_dir / Path(rel).name)

        lines = [
            f"Status: concluído",
            f"Linhas apuradas: {metrics.get('linhas_apuradas', result.get('linhas_apuradas', '—'))}",
            f"Lançamentos: {metrics.get('lancamentos_gerados', result.get('lancamentos_gerados', '—'))}",
            f"Reconciliação: {result.get('reconciliacao_status', '—')}",
        ]
        if self.result_workbook:
            lines.append(f"Arquivo: {self.result_workbook}")
        self._append_log("\n".join(lines))
        self.start_btn.configure(state=tk.NORMAL)
        self.open_btn.configure(state=tk.NORMAL if self.result_workbook else tk.DISABLED)
        self.folder_btn.configure(state=tk.NORMAL)
        messagebox.showinfo("Concluído", "Processamento finalizado com sucesso.")

    def _on_failed(self, message: str) -> None:
        self._append_log(f"ERRO: {message}")
        self.start_btn.configure(state=tk.NORMAL)
        job_store.clear_active_lock()
        messagebox.showerror("Falha", message)

    def _open_result(self) -> None:
        if self.result_workbook and self.result_workbook.exists():
            os.startfile(self.result_workbook)  # type: ignore[attr-defined]

    def _open_output_dir(self) -> None:
        path = self.output_dir
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)


def main() -> None:
    setup_runtime()
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except tk.TclError:
        pass
    DifalDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
