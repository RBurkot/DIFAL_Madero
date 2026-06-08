"""Janela de manutenção das regras NCM (ncm_regras.yaml)."""
from __future__ import annotations

import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

from difal_apuracao.ncm_rules import (
    _parse_date,
    load_regras_ncm_raw,
    ncm_regras_path,
    regra_vigente,
    save_regras_ncm,
)

METODOS = ("formula_padrao", "formula_coluna_z", "carga_bi", "carga_tributaria")


def _fmt_date(val) -> str:
    d = _parse_date(val)
    return d.strftime("%d/%m/%Y") if d else ""


def _parse_ui_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    return _parse_date(s)


def _status_vigencia(item: dict, hoje: date | None = None) -> str:
    from difal_apuracao.ncm_rules import _item_to_regra

    hoje = hoje or date.today()
    if regra_vigente(_item_to_regra(item), hoje):
        return "Vigente"
    return "Expirada"


class NcmRegrasEditor(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("Regras NCM — Manutenção")
        self.geometry("920x560")
        self.minsize(800, 480)
        self.transient(parent)

        self._regras: list[dict] = []
        self._selected_index: int | None = None

        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.BOTH, expand=True)

        path = ncm_regras_path()
        ttk.Label(top, text=f"Arquivo: {path}", foreground="#555").pack(anchor="w")

        tree_frm = ttk.Frame(top)
        tree_frm.pack(fill=tk.BOTH, expand=True, pady=8)
        cols = ("ncm", "carga", "metodo", "vigencia_fim", "status")
        self.tree = ttk.Treeview(tree_frm, columns=cols, show="headings", height=12)
        self.tree.heading("ncm", text="NCM")
        self.tree.heading("carga", text="Carga %")
        self.tree.heading("metodo", text="Método")
        self.tree.heading("vigencia_fim", text="Vigência fim")
        self.tree.heading("status", text="Status")
        self.tree.column("ncm", width=100)
        self.tree.column("carga", width=70)
        self.tree.column("metodo", width=120)
        self.tree.column("vigencia_fim", width=100)
        self.tree.column("status", width=80)
        scroll = ttk.Scrollbar(tree_frm, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        form = ttk.LabelFrame(top, text="Detalhe da regra", padding=8)
        form.pack(fill=tk.X, pady=4)

        self.ncm_var = tk.StringVar()
        self.carga_var = tk.StringVar()
        self.metodo_var = tk.StringVar(value=METODOS[0])
        self.ufs_var = tk.StringVar()
        self.excl_var = tk.StringVar()
        self.tipo_var = tk.StringVar()
        self.vig_ini_var = tk.StringVar()
        self.vig_fim_var = tk.StringVar()
        self.obs_var = tk.StringVar()

        def row(r, label, var, width=30, widget="entry"):
            ttk.Label(form, text=label).grid(row=r, column=0, sticky="w", **pad)
            if widget == "combo":
                w = ttk.Combobox(form, textvariable=var, values=list(METODOS), state="readonly", width=width)
            else:
                w = ttk.Entry(form, textvariable=var, width=width)
            w.grid(row=r, column=1, sticky="ew", **pad)
            return w

        row(0, "NCM", self.ncm_var, 16)
        row(1, "Carga tributária %", self.carga_var, 10)
        row(2, "Método novo DIFAL", self.metodo_var, 18, "combo")
        row(3, "UFs origem (vírgula)", self.ufs_var, 40)
        row(4, "UFs excluídas", self.excl_var, 20)
        row(5, "Tipo", self.tipo_var, 30)
        row(6, "Vigência início (DD/MM/AAAA)", self.vig_ini_var, 14)
        row(7, "Vigência fim (DD/MM/AAAA)", self.vig_fim_var, 14)
        row(8, "Observação", self.obs_var, 50)
        form.columnconfigure(1, weight=1)

        btn_frm = ttk.Frame(top)
        btn_frm.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frm, text="Nova regra", command=self._new_rule).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frm, text="Salvar regra", command=self._apply_form).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frm, text="Excluir", command=self._delete_rule).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frm, text="Gravar arquivo", command=self._save_file).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_frm, text="Recarregar", command=self._load_data).pack(side=tk.LEFT)

    def _load_data(self) -> None:
        self._regras = load_regras_ncm_raw()
        self._refresh_tree()
        self._clear_form()

    def _refresh_tree(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for i, item in enumerate(self._regras):
            vig_fim = _fmt_date(item.get("vigencia_fim"))
            self.tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(
                    item.get("ncm", ""),
                    item.get("carga_tributaria_pct", ""),
                    item.get("metodo_novo_difal", ""),
                    vig_fim or "—",
                    _status_vigencia(item),
                ),
            )

    def _clear_form(self) -> None:
        self._selected_index = None
        self.ncm_var.set("")
        self.carga_var.set("")
        self.metodo_var.set(METODOS[0])
        self.ufs_var.set("")
        self.excl_var.set("")
        self.tipo_var.set("")
        self.vig_ini_var.set("")
        self.vig_fim_var.set("")
        self.obs_var.set("")

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self._selected_index = idx
        item = self._regras[idx]
        self.ncm_var.set(str(item.get("ncm", "")))
        carga = item.get("carga_tributaria_pct")
        self.carga_var.set("" if carga is None else str(carga))
        self.metodo_var.set(item.get("metodo_novo_difal", METODOS[0]))
        ufs = item.get("ufs_origem") or []
        self.ufs_var.set(", ".join(ufs) if ufs else "")
        excl = item.get("exclusao_uf") or []
        self.excl_var.set(", ".join(excl) if excl else "")
        self.tipo_var.set(str(item.get("tipo", "")))
        self.vig_ini_var.set(_fmt_date(item.get("vigencia_inicio")))
        self.vig_fim_var.set(_fmt_date(item.get("vigencia_fim")))
        self.obs_var.set(str(item.get("observacao", "") or ""))

    def _parse_ufs(self, text: str) -> list[str] | None:
        parts = [p.strip().upper() for p in text.split(",") if p.strip()]
        return parts if parts else None

    def _form_to_dict(self) -> dict | None:
        ncm = self.ncm_var.get().strip()
        if not ncm:
            messagebox.showerror("Validação", "Informe o NCM.")
            return None
        try:
            carga = float(self.carga_var.get().replace(",", ".")) if self.carga_var.get().strip() else None
        except ValueError:
            messagebox.showerror("Validação", "Carga tributária inválida.")
            return None
        vig_ini = _parse_ui_date(self.vig_ini_var.get())
        vig_fim = _parse_ui_date(self.vig_fim_var.get())
        if self.vig_ini_var.get().strip() and vig_ini is None:
            messagebox.showerror("Validação", "Vigência início inválida. Use DD/MM/AAAA.")
            return None
        if self.vig_fim_var.get().strip() and vig_fim is None:
            messagebox.showerror("Validação", "Vigência fim inválida. Use DD/MM/AAAA.")
            return None
        if vig_ini and vig_fim and vig_fim < vig_ini:
            messagebox.showerror("Validação", "Vigência fim deve ser posterior ao início.")
            return None

        return {
            "ncm": ncm,
            "carga_tributaria_pct": carga,
            "ufs_origem": self._parse_ufs(self.ufs_var.get()),
            "exclusao_uf": self._parse_ufs(self.excl_var.get()) or [],
            "tipo": self.tipo_var.get().strip(),
            "metodo_novo_difal": self.metodo_var.get(),
            "vigencia_inicio": vig_ini.isoformat() if vig_ini else None,
            "vigencia_fim": vig_fim.isoformat() if vig_fim else None,
            "observacao": self.obs_var.get().strip() or None,
        }

    def _new_rule(self) -> None:
        self.tree.selection_remove(self.tree.selection())
        self._clear_form()

    def _apply_form(self) -> None:
        item = self._form_to_dict()
        if not item:
            return
        ncm = item["ncm"]
        if self._selected_index is None:
            if any(r.get("ncm") == ncm for r in self._regras):
                messagebox.showerror("Validação", f"NCM {ncm} já existe.")
                return
            self._regras.append(item)
            self._selected_index = len(self._regras) - 1
        else:
            old_ncm = self._regras[self._selected_index].get("ncm")
            if ncm != old_ncm and any(r.get("ncm") == ncm for r in self._regras):
                messagebox.showerror("Validação", f"NCM {ncm} já existe.")
                return
            self._regras[self._selected_index] = item
        self._refresh_tree()
        self.tree.selection_set(str(self._selected_index))

    def _delete_rule(self) -> None:
        if self._selected_index is None:
            messagebox.showinfo("Excluir", "Selecione uma regra.")
            return
        if not messagebox.askyesno("Excluir", "Remover a regra selecionada?"):
            return
        del self._regras[self._selected_index]
        self._selected_index = None
        self._refresh_tree()
        self._clear_form()

    def _save_file(self) -> None:
        if self.ncm_var.get().strip() and messagebox.askyesno(
            "Gravar", "Há dados no formulário não aplicados. Aplicar antes de gravar?"
        ):
            self._apply_form()
        try:
            path = save_regras_ncm(self._regras)
            messagebox.showinfo("Gravado", f"Regras salvas em:\n{path}")
        except OSError as e:
            messagebox.showerror("Erro", f"Não foi possível gravar: {e}")


def open_ncm_editor(parent: tk.Misc) -> None:
    NcmRegrasEditor(parent)
