"""Case history view: list, open and delete assessment cases."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from oracle.config import OracleConfig
from oracle.gui.theme import OLIVE, SUBHEADER
from oracle.models.case import Case
from oracle.services.engine import AssessmentEngine

_FONT = "Segoe UI"


class CasesView(ctk.CTkFrame):
    """Lists stored cases with open/delete actions."""

    def __init__(
        self,
        parent: object,
        config: OracleConfig,
        engine: AssessmentEngine,
        on_open: Callable[[str], None],
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.engine = engine
        self.on_open = on_open

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self, text="CASOS", font=(_FONT, 20, "bold"), text_color=OLIVE
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 4))
        hint = ctk.CTkLabel(
            self,
            text="Investigações locais armazenadas neste computador.",
            font=(_FONT, 12),
            text_color=SUBHEADER,
        )
        hint.grid(row=1, column=0, sticky="w", pady=(0, 12))

        ctk.CTkButton(
            self, text="Atualizar", width=110, command=self.refresh
        ).grid(row=0, column=1, sticky="ne", padx=(8, 0))

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=2, column=0, columnspan=2, sticky="nswe")

        self.refresh()

    def refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        cases = self.engine.manager.list_cases()
        if not cases:
            ctk.CTkLabel(
                self.scroll,
                text="Nenhum caso ainda: crie um pela opção 'Nova Análise'.",
                text_color=SUBHEADER,
            ).pack(padx=8, pady=24)
            return
        for case in cases:
            self._case_row(case)

    def _case_row(self, case: Case) -> None:
        frame = ctk.CTkFrame(self.scroll)
        frame.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(
            frame, text=case.name, font=(_FONT, 14, "bold")
        ).pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(
            frame,
            text=case.created_at.strftime("%Y-%m-%d %H:%M"),
            font=(_FONT, 11),
            text_color=SUBHEADER,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            frame,
            text="Abrir",
            width=84,
            height=28,
            command=lambda cid=case.id: self.on_open(cid),
        ).pack(side="right", padx=(6, 12), pady=6)
        ctk.CTkButton(
            frame,
            text="Excluir",
            width=84,
            height=28,
            fg_color="#8c2f2f",
            hover_color="#a03a3a",
            command=lambda: self._confirm_delete(case),
        ).pack(side="right", pady=6)

    def _confirm_delete(self, case: Case) -> None:
        ok = messagebox.askyesno(
            "Excluir caso",
            f"Excluir o caso '{case.name}' e todos os seus dados?",
        )
        if ok:
            self.engine.manager.delete_case(case.id)
            self.refresh()
