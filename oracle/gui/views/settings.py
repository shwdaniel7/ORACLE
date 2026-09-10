"""Settings view: configure ORACLE without touching files."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from oracle.config import OracleConfig
from oracle.gui.theme import OLIVE, SUBHEADER
from oracle.services.engine import AssessmentEngine

_FONT = "Segoe UI"


class SettingsView(ctk.CTkFrame):
    """Editable settings persisted back to ``~/.oracle/config.toml``."""

    def __init__(self, parent: object, config: OracleConfig) -> None:
        super().__init__(parent)
        self.config = config
        self.engine = AssessmentEngine(config)

        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text="CONFIGURAÇÕES", font=(_FONT, 20, "bold"), text_color=OLIVE
        ).grid(row=0, column=0, sticky="w", pady=(0, 18))

        body = ctk.CTkFrame(self)
        body.grid(row=1, column=0, sticky="nswe", padx=(0, 40))

        self._theme_var = ctk.StringVar(value=config.gui_theme)
        self._format_var = ctk.StringVar(value=config.default_report_format)
        self._collector_vars: dict[str, ctk.BooleanVar] = {}
        default_enabled = config.enabled_collectors

        row = 0
        self._label_row(body, row, "Aparência")
        ctk.CTkOptionMenu(
            body, values=["dark", "light"], variable=self._theme_var, width=220
        ).grid(row=row, column=1, sticky="w", padx=8, pady=6)
        row += 1

        self._label_row(body, row, "Formato padrão de relatório")
        ctk.CTkOptionMenu(
            body, values=["markdown", "json"], variable=self._format_var, width=220
        ).grid(row=row, column=1, sticky="w", padx=8, pady=6)
        row += 1

        self._label_row(body, row, "Coletores de descoberta (opt-in)")
        row += 1
        for collector in self.engine.collectors():
            enabled = (
                default_enabled is None or collector.name in default_enabled
            )
            variable = ctk.BooleanVar(value=enabled)
            self._collector_vars[collector.name] = variable
            ctk.CTkCheckBox(
                body,
                text=collector.display_name,
                variable=variable,
            ).grid(row=row, column=0, columnspan=2, sticky="w", padx=12, pady=3)
            ctk.CTkLabel(
                body, text=collector.description, font=(_FONT, 10), text_color=SUBHEADER
            ).grid(row=row, column=1, sticky="w", padx=8, pady=3)
            row += 1

        self._label_row(body, row, "Diretório de dados")
        ctk.CTkLabel(
            body, text=str(config.data_dir), font=(_FONT, 11), text_color=SUBHEADER
        ).grid(row=row, column=1, sticky="w", padx=8, pady=6)
        row += 1

        ctk.CTkButton(self, text="Salvar", width=140, command=self._save).grid(
            row=2, column=0, sticky="w", pady=(18, 0)
        )

    def _label_row(self, body: ctk.CTkFrame, row: int, text: str) -> None:
        ctk.CTkLabel(
            body, text=text, font=(_FONT, 13, "bold")
        ).grid(row=row, column=0, sticky="w", padx=12, pady=6)

    def _save(self) -> None:
        self.config.gui_theme = self._theme_var.get()
        self.config.default_report_format = self._format_var.get()
        self.config.enabled_collectors = tuple(
            name
            for name, variable in self._collector_vars.items()
            if variable.get()
        )
        self.config.save()
        messagebox.showinfo(
            "Salvo",
            "Configurações salvas. Reinicie o dashboard para aplicar a aparência.",
        )
