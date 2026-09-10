"""Application shell for the ORACLE dashboard.

A single window with an olive-green sidebar that routes between the
guided analysis wizard, the case history, and settings.
"""

from __future__ import annotations

import customtkinter as ctk

from oracle.config import OracleConfig
from oracle.gui.theme import OLIVE, OLIVE_HOVER, SUBHEADER, THEME_PATH
from oracle.gui.views.cases import CasesView
from oracle.gui.views.settings import SettingsView
from oracle.gui.wizard import WizardView
from oracle.services.engine import AssessmentEngine

_BRAND = "ORACLE"
_BRAND_LINE = "OBSERVATION · INTELLIGENCE · ANALYSIS"
_FONT = "Segoe UI"


class OracleApp(ctk.CTk):
    """Main dashboard window."""

    def __init__(self, config: OracleConfig) -> None:
        super().__init__()
        self.config = config
        self.engine = AssessmentEngine(config)
        self.title(f"{_BRAND} — Personal OPSEC Intelligence Engine")
        self.geometry("1120x740")
        self.minsize(920, 620)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nswe")
        self._sidebar.grid_rowconfigure(6, weight=1)

        self.content: ctk.CTkFrame | None = None
        self._build_sidebar()
        self.show_wizard()

    def _build_sidebar(self) -> None:
        brand = ctk.CTkLabel(
            self._sidebar,
            text=_BRAND,
            font=(_FONT, 24, "bold"),
            text_color=OLIVE,
        )
        brand.pack(pady=(28, 2))
        line = ctk.CTkLabel(
            self._sidebar,
            text=_BRAND_LINE,
            font=(_FONT, 10),
            text_color=SUBHEADER,
            wraplength=180,
        )
        line.pack(pady=(0, 26))

        for label, target in (
            ("Nova Análise", self.show_wizard),
            ("Casos", self.show_cases),
            ("Configurações", self.show_settings),
        ):
            ctk.CTkButton(
                self._sidebar,
                text=label,
                command=target,
                corner_radius=0,
                height=42,
                fg_color="transparent",
                hover_color=OLIVE_HOVER,
            ).pack(fill="x")

    def set_content(self, frame: ctk.CTkFrame) -> None:
        """Swap the main content area, disposing the previous view."""
        if self.content is not None:
            self.content.destroy()
        self.content = frame
        self.content.grid(row=0, column=1, sticky="nswe", padx=18, pady=18)

    def show_wizard(self, case_id: str | None = None) -> None:
        self.set_content(WizardView(self, self.config, self.engine, case_id))

    def show_cases(self) -> None:
        self.set_content(
            CasesView(
                self,
                self.config,
                self.engine,
                on_open=self.show_wizard,
            )
        )

    def show_settings(self) -> None:
        self.set_content(SettingsView(self, self.config))


def build_app(config: OracleConfig) -> ctk.CTk:
    """Configure the theme and build the main window."""
    ctk.set_appearance_mode(config.gui_theme)
    ctk.set_default_color_theme(str(THEME_PATH))
    app = OracleApp(config)
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    return app
