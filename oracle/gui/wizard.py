"""Guided analysis wizard: the friendly, CLI-free ORACLE workflow.

Six steps follow the assessment pipeline:

1. New Case → 2. Identities → 3. Discovery → 4. Review → 5. Result
→ 6. Remediation & Report.

Discovery runs in a background thread so the interface never freezes;
progress is streamed back to the UI through a queue.
"""

from __future__ import annotations

import hashlib
import queue
import threading
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from oracle.config import OracleConfig
from oracle.gui.theme import DANGER, OLIVE, SUBHEADER, WARN
from oracle.models import Case, Finding, Identity, IdentityType, Severity
from oracle.reports.generator import AssessmentBundle
from oracle.services.engine import AssessmentEngine, ScanProgress

_FONT = "Segoe UI"
_STEP_TITLES = (
    "Novo Caso",
    "Identidades",
    "Descoberta",
    "Revisão",
    "Resultado",
    "Remediação",
)
_IDENTITY_TYPES = [item.value for item in IdentityType]

_SEVERITY_COLORS = {
    Severity.CRITICAL.value: "#b00020",
    Severity.HIGH.value: DANGER,
    Severity.MEDIUM.value: WARN,
    Severity.LOW.value: OLIVE,
}


class WizardView(ctk.CTkFrame):
    """Six-step guided assessment flow."""

    def __init__(
        self,
        parent: object,
        config: OracleConfig,
        engine: AssessmentEngine,
        case_id: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.engine = engine
        self.case_id = case_id
        self.bundle: AssessmentBundle | None = None

        self.step = 1
        self._running = False
        self._scan_ran = False
        self._destroyed = False
        self._status_counts: dict[str, int] = {}
        self._queue: queue.Queue[object] = queue.Queue()
        self._cancel_event = threading.Event()

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self._header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._header.grid(row=0, column=0, sticky="ew")
        self._step_labels: list[ctk.CTkLabel] = []
        for index, title in enumerate(_STEP_TITLES, start=1):
            label = ctk.CTkLabel(
                self._header,
                text=f"{index}. {title}",
                font=(_FONT, 13, "bold"),
            )
            label.pack(side="left", padx=(0, 18))
            self._step_labels.append(label)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nswe")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._footer = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._footer.grid(row=2, column=0, sticky="ew")
        self._back_button = ctk.CTkButton(
            self._footer, text="← Voltar", width=120, command=self._go_back
        )
        self._back_button.pack(side="left", pady=12)
        self._next_button = ctk.CTkButton(
            self._footer, text="Continuar →", width=140, command=self._go_forward
        )
        self._next_button.pack(side="right", pady=12)

        self._render()

    # ------------------------------------------------------------------ step
    def _render(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()
        for index, label in enumerate(self._step_labels, start=1):
            label.configure(
                text_color=OLIVE if index == self.step else SUBHEADER
            )

        if self.case_id is not None and self.bundle is None:
            self.bundle = self.engine.manager.build_bundle(self.case_id)

        if self.step == 1:
            self._step_new_case()
        elif self.step == 2:
            self._step_identities()
        elif self.step == 3:
            self._step_discovery()
        elif self.step == 4:
            self._step_review()
        elif self.step == 5:
            self._step_result()
        else:
            self._step_remediation()

        self._back_button.configure(state="normal" if self.step > 1 else "disabled")
        self._next_button.configure(
            text="Finalizar" if self.step == 6 else "Continuar →",
            state="normal" if not self._running else "disabled",
        )

    def _go_back(self) -> None:
        if self._running or self.step <= 1:
            return
        self.step -= 1
        self._render()

    def _go_forward(self) -> None:
        if self._running or self._destroyed:
            return
        if self.step == 6:
            self._finish()
            return
        if self.step == 1:
            created = self._create_case()
            if created is None:
                return
        self.step += 1
        self._render()

    def _finish(self) -> None:
        handler = getattr(self.master, "show_wizard", None)
        if callable(handler):
            handler()

    def destroy(self) -> None:
        """Mark the view as gone so orphaned timers/threads touch nothing."""
        self._destroyed = True
        super().destroy()

    def _step_new_case(self) -> None:
        if self.case_id is not None:
            case = self.engine.manager.get_case(self.case_id)
            ctk.CTkLabel(
                self.content, text="CASO", font=(_FONT, 22, "bold"), text_color=OLIVE
            ).pack(pady=(0, 6))
            ctk.CTkLabel(
                self.content,
                text=case.name,
                font=(_FONT, 16),
            ).pack(pady=(0, 12))
            return

        ctk.CTkLabel(
            self.content, text="NOVO CASO", font=(_FONT, 22, "bold"), text_color=OLIVE
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            self.content,
            text="Cada avaliação é um caso isolado: o que é observado aqui não se mistura com outras investigações.",
            font=(_FONT, 12),
            text_color=SUBHEADER,
            wraplength=560,
        ).pack(pady=(0, 24))

        ctk.CTkLabel(self.content, text="Nome do caso", font=(_FONT, 13, "bold")).pack(
            anchor="w", padx=60
        )
        self._name_entry = ctk.CTkEntry(self.content, width=480, placeholder_text="ex.: Minha auditoria pessoal")
        self._name_entry.pack(pady=(4, 12), padx=60)
        self._name_entry.focus_set()

        ctk.CTkLabel(
            self.content, text="Descrição (opcional)", font=(_FONT, 13, "bold")
        ).pack(anchor="w", padx=60)
        self._description_entry = ctk.CTkEntry(self.content, width=480, placeholder_text="Por que você está avaliando?")
        self._description_entry.pack(pady=(4, 0), padx=60)

    def _create_case(self) -> Case | None:
        name = self._name_entry.get().strip()
        if not name:
            messagebox.showwarning("Nome obrigatório", "Informe um nome para o caso.")
            return None
        description = self._description_entry.get().strip() or None
        case = self.engine.manager.create_case(name, description)
        self.case_id = case.id
        self.bundle = self.engine.manager.build_bundle(case.id)
        return case

    # ----------------------------------------------------------- step 2
    def _step_identities(self) -> None:
        ctk.CTkLabel(
            self.content, text="IDENTIDADES", font=(_FONT, 22, "bold"), text_color=OLIVE
        ).pack(pady=(0, 16))
        if self.case_id is None:
            return

        form = ctk.CTkFrame(self.content)
        form.pack(fill="x", padx=60, pady=(0, 16))

        self._identity_type_var = ctk.StringVar(value=_IDENTITY_TYPES[0])
        ctk.CTkOptionMenu(
            form, values=_IDENTITY_TYPES, variable=self._identity_type_var, width=130
        ).pack(side="left", padx=(0, 8))
        self._identity_entry = ctk.CTkEntry(
            form, width=300, placeholder_text="ex.: meu_usuario, eu@exemplo.com, meudominio.com"
        )
        self._identity_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(form, text="Adicionar", width=100, command=self._add_identity).pack(
            side="left"
        )
        ctk.CTkLabel(
            self.content,
            text=(
                "Senhas são mascaradas e guardadas só como hash local; a verificação "
                "usa Pwned Passwords (k-anonymity) e nada além do prefixo do hash sai "
                "do computador."
            ),
            font=(_FONT, 11),
            text_color=SUBHEADER,
            wraplength=600,
            justify="left",
        ).pack(fill="x", padx=60, pady=(0, 16))

        self._identity_list = ctk.CTkScrollableFrame(self.content, height=300)
        self._identity_list.pack(fill="x", padx=60)
        self._render_identity_list()

    def _add_identity(self) -> None:
        if self.case_id is None:
            return
        value = self._identity_entry.get().strip()
        if not value:
            messagebox.showwarning("Valor obrigatório", "Informe o identificador.")
            return
        identity_type = IdentityType(self._identity_type_var.get())
        if identity_type is IdentityType.PASSWORD:
            value = hashlib.sha1(value.encode("utf-8")).hexdigest()
        self.engine.manager.add_identity(
            self.case_id, Identity(type=identity_type, value=value)
        )
        self._identity_entry.delete(0, "end")
        self._render_identity_list()

    def _render_identity_list(self) -> None:
        for child in self._identity_list.winfo_children():
            child.destroy()
        if self.case_id is None:
            return
        identities = self.engine.manager.list_identities(self.case_id)
        if not identities:
            ctk.CTkLabel(
                self._identity_list,
                text="Nenhuma identidade ainda. Adicione um username, email ou domínio.",
                text_color=SUBHEADER,
            ).pack(padx=8, pady=16)
            return
        for identity in identities:
            row = ctk.CTkFrame(self._identity_list)
            row.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(
                row, text=identity.type.value, width=96, font=(_FONT, 12, "bold")
            ).pack(side="left", padx=10, pady=6)
            value = identity.value
            if identity.type is IdentityType.PASSWORD:
                value = f"sha1:{value[:10]}… (hash armazenado)"
            ctk.CTkLabel(row, text=value, font=(_FONT, 13)).pack(side="left", padx=6)

    # ----------------------------------------------------------- step 3
    def _step_discovery(self) -> None:
        ctk.CTkLabel(
            self.content, text="DESCOBERTA", font=(_FONT, 22, "bold"), text_color=OLIVE
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            self.content,
            text="Probes de presença contra fontes públicas, somente sobre suas próprias identidades. Nada é coletado além do que é observado.",
            font=(_FONT, 12),
            text_color=SUBHEADER,
            wraplength=620,
        ).pack(pady=(0, 16))

        enabled = self.engine.settings.enabled_collectors
        self._collector_vars: dict[str, ctk.BooleanVar] = {}
        frame = ctk.CTkFrame(self.content)
        frame.pack(fill="x", padx=60, pady=(0, 14))
        for collector in self.engine.collectors():
            variable = ctk.BooleanVar(value=collector.name in enabled)
            self._collector_vars[collector.name] = variable
            ctk.CTkCheckBox(
                frame, text=collector.display_name, variable=variable
            ).pack(anchor="w", padx=12, pady=2)
            ctk.CTkLabel(
                frame, text=collector.description, font=(_FONT, 10), text_color=SUBHEADER
            ).pack(anchor="w", padx=(30, 12), pady=(0, 4))

        if not self.engine.manager.list_identities(self.case_id or ""):
            ctk.CTkLabel(
                self.content,
                text="Você ainda não adicionou identidades. A descoberta só roda sobre identidades registradas.",
                font=(_FONT, 12),
                text_color=WARN,
            ).pack(pady=(0, 12))

        self._progress_bar = ctk.CTkProgressBar(self.content, height=14)
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", padx=60, pady=(0, 10))

        self._log = ctk.CTkTextbox(self.content, height=170, state="disabled")
        self._log.pack(fill="x", padx=60)

        self._summary_label = ctk.CTkLabel(
            self.content,
            text="",
            font=(_FONT, 11),
            text_color=SUBHEADER,
            wraplength=620,
            justify="left",
        )
        self._summary_label.pack(fill="x", padx=60, pady=(8, 0))

        self._warn_label = ctk.CTkLabel(
            self.content,
            text="",
            font=(_FONT, 11),
            text_color=WARN,
            wraplength=620,
            justify="left",
        )
        self._warn_label.pack(fill="x", padx=60, pady=(2, 0))

        buttons = ctk.CTkFrame(self.content, fg_color="transparent")
        buttons.pack(pady=(12, 0))
        self._run_button = ctk.CTkButton(
            buttons, text="▶ Rodar descoberta", width=170, command=self._start_scan
        )
        self._run_button.pack(side="left", padx=6)
        self._cancel_button = ctk.CTkButton(
            buttons, text="Parar", width=100, state="disabled", command=self._cancel_scan
        )
        self._cancel_button.pack(side="left", padx=6)

        if (
            self.case_id is not None
            and not self._scan_ran
            and self.engine.manager.list_identities(self.case_id)
        ):
            self.after(300, self._start_scan)

    def _start_scan(self) -> None:
        if self._destroyed or self._running or self.case_id is None or self.step != 3:
            return
        names = [n for n, variable in self._collector_vars.items() if variable.get()]
        if not names:
            messagebox.showwarning("Coletores", "Selecione ao menos um coletor.")
            return
        self._running = True
        self._cancel_event.clear()
        self._run_button.configure(state="disabled")
        self._cancel_button.configure(state="normal")
        self._next_button.configure(state="disabled")
        self._progress_bar.set(0)
        self._status_counts = {}
        self._summary_label.configure(text="")
        self._refresh_coverage_warning()
        self._append_log("Descoberta iniciada...\n")
        payload = (self.case_id, names)
        threading.Thread(
            target=self._scan_worker, args=(payload,), daemon=True
        ).start()
        self.after(80, self._poll)

    def _scan_worker(self, payload: tuple[str, list[str]]) -> None:
        try:
            case_id, names = payload
            self.engine.scan(
                case_id,
                collector_names=names,
                progress=lambda event: self._queue.put(event),
                cancel=lambda: self._cancel_event.is_set(),
            )
            self.engine.analyze(case_id)
            self._queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001 - surface to the UI
            self._queue.put(("error", f"{exc}\n{traceback.format_exc()}"))

    def _poll(self) -> None:
        if self._destroyed:
            return
        alive = self.step == 3 and self.content.winfo_exists()
        try:
            item = self._queue.get_nowait()
        except queue.Empty:
            if self._running:
                self.after(80, self._poll)
            return

        if isinstance(item, ScanProgress):
            status = item.status if item.status else "OK"
            self._status_counts[status] = self._status_counts.get(status, 0) + 1
            if alive:
                fraction = (
                    1.0 if item.total == 0 else item.completed / max(item.total, 1)
                )
                self._progress_bar.set(fraction)
                self._append_log(
                    f"[{item.completed}/{item.total}] {item.source or '?'}: "
                    f"{item.identifier or '?'} → {status}"
                    + (f" — {item.detail}" if item.detail else "")
                    + "\n"
                )
            self.after(80, self._poll)
        elif isinstance(item, tuple) and item[0] == "done":
            self._running = False
            self._scan_ran = True
            if alive:
                self._append_log("\nDescoberta concluída.\n")
                self._run_button.configure(state="normal")
                self._cancel_button.configure(state="disabled")
                self._next_button.configure(state="normal")
                self._refresh_coverage_warning()
                self._summary_label.configure(text=self._scan_summary_text())
            if self.case_id is not None:
                self.bundle = self.engine.manager.build_bundle(self.case_id)
        elif isinstance(item, tuple) and item[0] == "error":
            self._running = False
            if alive:
                self._append_log("\nErro na descoberta.\n")
                self._run_button.configure(state="normal")
                self._cancel_button.configure(state="disabled")
                self._next_button.configure(state="normal")
                messagebox.showerror("Descoberta", str(item[1]))

    def _cancel_scan(self) -> None:
        if self._destroyed:
            return
        self._cancel_event.set()
        self._append_log("Cancelamento solicitado...\n")

    def _append_log(self, text: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", text)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _refresh_coverage_warning(self) -> None:
        if self.case_id is None or not hasattr(self, "_warn_label"):
            return
        collectors = {c.name: c for c in self.engine.collectors()}
        covered: set[IdentityType] = set()
        for name, variable in getattr(self, "_collector_vars", {}).items():
            if variable.get() and name in collectors:
                covered.update(collectors[name].supported_identifiers)
        identities = self.engine.manager.list_identities(self.case_id)
        skipped = [
            f"{identity.type.value}: {identity.value}"
            for identity in identities
            if identity.type not in covered
        ]
        if skipped and not self._running:
            text = (
                "Sem coletor para: "
                + ", ".join(skipped)
                + " — nada será verificado para estes itens."
            )
        elif skipped:
            text = "Sem coletor para: " + ", ".join(skipped) + " — estes itens serão pulados."
        else:
            text = ""
        self._warn_label.configure(text=text)

    def _scan_summary_text(self) -> str:
        found = self._status_counts.get("FOUND", 0)
        not_seen = self._status_counts.get("NOT_FOUND", 0)
        failed = self._status_counts.get("ERROR", 0) + self._status_counts.get(
            "UNKNOWN", 0
        )
        total = len(self._status_counts)
        if total == 0:
            return (
                "Nenhuma verificação foi executada. "
                "Confirme se há identidades registradas e se ao menos um coletor está marcado."
            )
        lines = [
            f"{found} encontrado(s) · {not_seen} dos quais nada foi observado · "
            f"{failed} com erro/indefinido (rate-limit ou fonte indisponível).",
            "",
            "Nada observado NÃO significa que não exista: as fontes confirmam presença, "
            "nunca verificam ausência.",
        ]
        if failed:
            lines.append(
                "Fontes com erro (rate-limit/indisponíveis) não geram achado por segurança "
                "— execute novamente mais tarde para confirmar."
            )
        return "\n".join(lines)

    # ----------------------------------------------------------- step 4
    def _step_review(self) -> None:
        ctk.CTkLabel(
            self.content, text="REVISÃO", font=(_FONT, 22, "bold"), text_color=OLIVE
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            self.content,
            text="Avatar a seguir. Você pode descartar achados que não fizerem sentido, ou rodar a descoberta novamente.",
            font=(_FONT, 12),
            text_color=SUBHEADER,
        ).pack(pady=(0, 14))

        scroll = ctk.CTkScrollableFrame(self.content, height=400)
        scroll.pack(fill="both", expand=True, padx=40)
        findings = self.engine.manager.list_findings(self.case_id or "")
        if not findings:
            ctk.CTkLabel(
                scroll, text="Nenhum achado registrado ainda.", text_color=SUBHEADER
            ).pack(pady=24)
            return
        for finding in findings:
            self._finding_row(scroll, finding)

    def _finding_row(self, parent: ctk.CTkFrame, finding: Finding) -> None:
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=4, pady=4)
        color = _SEVERITY_COLORS.get(finding.severity.value, OLIVE)
        ctk.CTkLabel(
            row, text=finding.severity.value, width=84, text_color=color,
            font=(_FONT, 12, "bold"),
        ).pack(side="left", padx=10, pady=8)
        body = ctk.CTkFrame(row, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True, padx=6)
        ctk.CTkLabel(
            body,
            text=f"[{finding.confidence.value}] {finding.category}",
            font=(_FONT, 12, "bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            body, text=finding.description, font=(_FONT, 11), text_color=SUBHEADER
        ).pack(anchor="w")
        ctk.CTkButton(
            row,
            text="Descartar",
            width=90,
            height=28,
            fg_color="#8c2f2f",
            hover_color="#a03a3a",
            command=lambda fid=finding.id: self._discard_finding(fid),
        ).pack(side="right", padx=10, pady=8)

    def _discard_finding(self, finding_id: str) -> None:
        if self.case_id is None:
            return
        self.engine.manager.delete_finding(self.case_id, finding_id)
        self.bundle = self.engine.manager.build_bundle(self.case_id)
        self._render()

    # ----------------------------------------------------------- step 5
    def _step_result(self) -> None:
        ctk.CTkLabel(
            self.content, text="RESULTADO", font=(_FONT, 22, "bold"), text_color=OLIVE
        ).pack(pady=(0, 14))
        bundle = self.bundle or self.engine.manager.build_bundle(self.case_id or "")
        overall = bundle.score.overall
        ctk.CTkLabel(
            self.content, text=str(overall), font=(_FONT, 58, "bold"), text_color=OLIVE
        ).pack()
        ctk.CTkLabel(
            self.content,
            text=f"/ 100 — pontuação OPSEC de {bundle.case.name}",
            font=(_FONT, 13),
            text_color=SUBHEADER,
        ).pack(pady=(0, 16))

        frame = ctk.CTkFrame(self.content)
        frame.pack(fill="x", padx=60)
        if not bundle.findings:
            ctk.CTkLabel(
                frame,
                text=(
                    "Nenhum achado de exposição foi observado pelas fontes consultadas.\n\n"
                    "Isso não significa que não existam informações públicas: apenas que "
                    "nenhuma fonte confirmou presença para os identificadores informados.\n\n"
                    "Volte à etapa 'Descoberta', confirme os coletores marcados (erros de "
                    "rate-limit não geram achado) e tente novamente."
                ),
                font=(_FONT, 12),
                text_color=SUBHEADER,
                justify="left",
                wraplength=560,
            ).pack(anchor="w", padx=16, pady=(0, 12))
            return
        for dimension, score in bundle.score.dimensions.items():
            ctk.CTkLabel(
                frame, text=dimension, font=(_FONT, 12), width=220
            ).pack(anchor="w", padx=(16, 0), pady=(6, 0))
            bar = ctk.CTkProgressBar(frame, height=10)
            bar.set(score / 100)
            bar.pack(fill="x", padx=16, pady=(2, 4))

        relationships = bundle.relationships
        if relationships:
            ctk.CTkLabel(
                frame,
                text="\nCorrelações detectadas:",
                font=(_FONT, 13, "bold"),
            ).pack(anchor="w", padx=16, pady=(14, 0))
            for relationship in relationships:
                ctk.CTkLabel(
                    frame,
                    text=f"{relationship.identity_a_id[:8]} ↔ "
                    f"{relationship.identity_b_id[:8]} ({relationship.relationship_type})",
                    font=(_FONT, 11),
                    text_color=SUBHEADER,
                ).pack(anchor="w", padx=16)

    # ----------------------------------------------------------- step 6
    def _step_remediation(self) -> None:
        ctk.CTkLabel(
            self.content, text="REMEDIAÇÃO", font=(_FONT, 22, "bold"), text_color=OLIVE
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            self.content,
            text="Plano priorizado de ações. Marque o que já resolveu e gere o relatório.",
            font=(_FONT, 12),
            text_color=SUBHEADER,
        ).pack(pady=(0, 14))

        scroll = ctk.CTkScrollableFrame(self.content, height=320)
        scroll.pack(fill="both", expand=True, padx=40)
        bundle = self.bundle or self.engine.manager.build_bundle(self.case_id or "")
        has_items = any(items for _, items in bundle.remediation.items())
        if not has_items:
            ctk.CTkLabel(
                scroll,
                text=(
                    "Nenhum achado foi registrado ainda, então ainda não há ações a "
                    "remediar.\n\n"
                    "A remediação é gerada a partir da Descoberta: se já rodou a etapa "
                    "'Descoberta' e mesmo assim nada aparece aqui, é porque nenhuma "
                    "fonte confirmou presença (ou todas falharam por rate-limit). "
                    "Revise o resumo da descoberta e rode novamente.\n\n"
                    "Quando houver achados, este plano mostrará ações priorizadas."
                ),
                font=(_FONT, 12),
                text_color=SUBHEADER,
                justify="left",
                wraplength=560,
            ).pack(anchor="w", padx=8, pady=12)
        else:
            for priority, items in bundle.remediation.items():
                if not items:
                    continue
                ctk.CTkLabel(
                    scroll, text=priority, font=(_FONT, 14, "bold"), text_color=OLIVE
                ).pack(anchor="w", pady=(10, 4))
                for item in items:
                    row = ctk.CTkFrame(scroll, fg_color="transparent")
                    row.pack(fill="x", anchor="w", padx=8, pady=2)
                    ctk.CTkCheckBox(row, text="").pack(side="left", padx=(0, 6))
                    ctk.CTkLabel(
                        row,
                        text=item,
                        font=(_FONT, 12),
                        justify="left",
                        wraplength=560,
                        anchor="w",
                    ).pack(side="left", fill="x", expand=True)

        footer = ctk.CTkFrame(self.content, fg_color="transparent")
        footer.pack(fill="x", padx=40, pady=(14, 0))
        self._format_var = ctk.StringVar(
            value=self.config.default_report_format
        )
        ctk.CTkOptionMenu(
            footer, values=["markdown", "json"], variable=self._format_var, width=140
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            footer, text="Salvar relatório", width=160, command=self._generate_report
        ).pack(side="left")

    def _generate_report(self) -> None:
        if self.case_id is None:
            return
        fmt = self._format_var.get()
        bundle = self.bundle or self.engine.manager.build_bundle(self.case_id)
        content = bundle.to_json() if fmt == "json" else bundle.to_markdown()
        extension = "json" if fmt == "json" else "md"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{extension}",
            filetypes=[(fmt.upper(), f"*.{extension}"), ("Todos os arquivos", "*.*")],
            initialfile=f"oracle-assessment.{extension}",
        )
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        messagebox.showinfo("Relatório", f"Relatório salvo em:\n{path}")
