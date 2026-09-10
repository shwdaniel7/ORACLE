"""Command-line interface for ORACLE."""

from __future__ import annotations

import sys
from contextlib import suppress
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from oracle.__about__ import __version__
from oracle.analyzers.correlation import build_correlation_plan
from oracle.case.manager import CaseManager
from oracle.config import OracleConfig
from oracle.models import (
    Confidence,
    Evidence,
    Finding,
    Identity,
    IdentityType,
    Relationship,
    Severity,
)
from oracle.services.engine import AssessmentEngine, ScanProgress

_BRAND = "ORACLE"
_SUBTITLE = "PERSONAL OPSEC INTELLIGENCE ENGINE"
_BRAND_LINE = "OBSERVATION · INTELLIGENCE · ANALYSIS"
_OLIVE = "#6b8e23"

console = Console()


def _configure_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        with suppress(AttributeError, OSError):
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


def _service() -> tuple[OracleConfig, CaseManager]:
    config = OracleConfig.load()
    return config, CaseManager(config)


def _banner() -> str:
    return f"[bold {_OLIVE}]{_BRAND}[/] {_SUBTITLE}\n[dim]{_BRAND_LINE}[/]"


def _identities_table(identities: list[Identity]) -> Table:
    table = Table(title="Identities", show_header=True, header_style=f"bold {_OLIVE}")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Value")
    table.add_column("Label")
    for identity in identities:
        table.add_row(
            identity.id,
            identity.type.value,
            identity.value,
            identity.label or "",
        )
    return table


def _findings_table(findings: list[Finding]) -> Table:
    table = Table(title="Findings", show_header=True, header_style=f"bold {_OLIVE}")
    table.add_column("ID", style="dim")
    table.add_column("Category")
    table.add_column("Severity")
    table.add_column("Confidence")
    table.add_column("Description")
    for finding in findings:
        table.add_row(
            finding.id,
            finding.category,
            finding.severity.value,
            finding.confidence.value,
            finding.description,
        )
    return table


def _relationships_table(relationships: list[Relationship]) -> Table:
    table = Table(
        title="Relationships", show_header=True, header_style=f"bold {_OLIVE}"
    )
    table.add_column("ID", style="dim")
    table.add_column("Identity A")
    table.add_column("Identity B")
    table.add_column("Type")
    table.add_column("Confidence")
    for relationship in relationships:
        table.add_row(
            relationship.id,
            relationship.identity_a_id,
            relationship.identity_b_id,
            relationship.relationship_type,
            relationship.confidence.value,
        )
    return table


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="oracle")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ORACLE — Personal OPSEC Intelligence Engine.

    OBSERVATION · INTELLIGENCE · ANALYSIS

    Run without arguments to open the graphical dashboard.
    """
    _configure_encoding()
    if ctx.invoked_subcommand is None:
        ctx.invoke(dashboard_command)


@cli.command("init")
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory where cases and the assessment database are stored.",
)
def init_command(data_dir: Path | None) -> None:
    """Initialize configuration and local storage."""
    config = OracleConfig.load(data_dir=data_dir)
    config.save()
    CaseManager(config)
    console.print(_banner())
    console.print(
        Panel.fit(
            f"Data directory: [bold]{config.data_dir}[/]\n"
            f"Database: [bold]{config.database_path}[/]",
            style=_OLIVE,
        )
    )


@cli.command("version")
def version_command() -> None:
    """Show the installed version."""
    console.print(f"{_BRAND} {__version__} — {_SUBTITLE}")


@cli.command("dashboard")
def dashboard_command() -> None:
    """Open the graphical ORACLE dashboard."""
    try:
        from oracle.gui.app import build_app
    except ModuleNotFoundError as exc:
        raise click.ClickException(
            'The dashboard requires the "gui" optional dependencies. '
            'Install them with `pip install -e ".[gui]"`.'
        ) from exc
    config = OracleConfig.load()
    build_app(config).mainloop()


def _print_scan_progress(event: ScanProgress) -> None:
    flow = f"[dim]({event.completed}/{event.total})[/] "
    name = event.source or "?"
    identifier = event.identifier or "?"
    console.print(f"{flow}{name}: {identifier} → {event.status}" + (
        f" — {event.detail}" if event.detail else ""
    ))


@cli.command("scan")
@click.argument("case_id")
@click.option(
    "--collector",
    "collector_names",
    multiple=True,
    help="Restrict the scan to specific collectors (repeatable).",
)
@click.option(
    "--no-save",
    is_flag=True,
    help="Show results without persisting findings.",
)
def scan_command(
    case_id: str,
    collector_names: tuple[str, ...],
    no_save: bool,
) -> None:
    """Run public-information discovery (probes) for a case."""
    try:
        config, manager = _service()
        engine = AssessmentEngine(config, manager)
        created = engine.scan(
            case_id,
            collector_names=collector_names or None,
            persist=not no_save,
            progress=_print_scan_progress,
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    verb = "reported" if no_save else "saved"
    console.print(
        Panel.fit(
            f"Scan complete: [bold]{len(created)}[/] finding(s) {verb}.",
            style=f"bold {_OLIVE}",
        )
    )


@cli.command("analyze")
@click.argument("case_id")
@click.option(
    "--no-save",
    is_flag=True,
    help="Show the correlation plan without persisting it.",
)
def analyze_command(case_id: str, no_save: bool) -> None:
    """Run correlation analysis over a case's findings."""
    try:
        config, manager = _service()
        engine = AssessmentEngine(config, manager)
        if no_save:
            plan = build_correlation_plan(
                manager.list_identities(case_id),
                manager.list_findings(case_id),
            )
            relationships = list(plan.relationships)
        else:
            relationships = engine.analyze(case_id)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    if not relationships:
        console.print("[dim]No correlations detected.[/]")
        return
    console.print(_relationships_table(relationships))


@cli.group("case")
def case_group() -> None:
    """Manage assessment cases."""


@case_group.command("new")
@click.argument("name")
@click.option("--description", default=None, help="Optional case description.")
def case_new(name: str, description: str | None) -> None:
    """Create a new assessment case."""
    _, manager = _service()
    case = manager.create_case(name, description)
    console.print(
        Panel.fit(
            f"[bold]Case created[/]\nID: {case.id}\nName: {case.name}",
            style=f"bold {_OLIVE}",
        )
    )


@case_group.command("list")
def case_list() -> None:
    """List all assessment cases."""
    _, manager = _service()
    cases = manager.list_cases()
    table = Table(title="Cases", show_header=True, header_style=f"bold {_OLIVE}")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Created", style="dim")
    for case in cases:
        table.add_row(
            case.id,
            case.name,
            case.created_at.strftime("%Y-%m-%d %H:%M"),
        )
    console.print(table)


@case_group.command("show")
@click.argument("case_id")
def case_show(case_id: str) -> None:
    """Show the details of a case."""
    try:
        _, manager = _service()
        case = manager.get_case(case_id)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(
        Panel.fit(
            f"[bold]{case.name}[/]\nID: {case.id}\n"
            f"Created: {case.created_at:%Y-%m-%d %H:%M} — "
            f"Updated: {case.updated_at:%Y-%m-%d %H:%M}"
            + (f"\n[dim]{case.description}[/]" if case.description else ""),
            title="Case",
            style=_OLIVE,
        )
    )
    console.print(_identities_table(manager.list_identities(case_id)))
    console.print(_findings_table(manager.list_findings(case_id)))
    console.print(_relationships_table(manager.list_relationships(case_id)))


@case_group.command("delete")
@click.argument("case_id")
@click.option("--force", is_flag=True, help="Delete without confirmation.")
def case_delete(case_id: str, force: bool) -> None:
    """Delete a case and all of its data."""
    try:
        _, manager = _service()
        if not force:
            click.confirm(
                f"Delete case {case_id} and all associated data?",
                abort=True,
            )
        manager.delete_case(case_id)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(f"Case [bold]{case_id}[/] deleted.")


@cli.group("identity")
def identity_group() -> None:
    """Manage identities within a case."""


@identity_group.command("add")
@click.argument("case_id")
@click.option(
    "--type",
    "type_",
    type=click.Choice([t.value for t in IdentityType], case_sensitive=False),
    required=True,
    help="Kind of identifier.",
)
@click.option("--value", required=True, help="The identifier value.")
@click.option("--label", default=None, help="Optional display label.")
def identity_add(case_id: str, type_: str, value: str, label: str | None) -> None:
    """Add an identity to a case."""
    try:
        _, manager = _service()
        identity = manager.add_identity(
            case_id,
            Identity(type=IdentityType(type_), value=value, label=label),
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(
        f"Identity [bold]{identity.value}[/] "
        f"([dim]{type_}[/]) added as [dim]{identity.id}[/]."
    )


@identity_group.command("list")
@click.argument("case_id")
def identity_list(case_id: str) -> None:
    """List identities in a case."""
    try:
        _, manager = _service()
        identities = manager.list_identities(case_id)
        if not identities:
            console.print("[dim]No identities recorded.[/]")
            return
        console.print(_identities_table(identities))
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.group("finding")
def finding_group() -> None:
    """Manage OPSEC findings within a case."""


@finding_group.command("add")
@click.argument("case_id")
@click.option("--category", required=True, help="Finding category.")
@click.option(
    "--severity",
    type=click.Choice([s.value for s in Severity], case_sensitive=False),
    required=True,
)
@click.option(
    "--confidence",
    type=click.Choice([c.value for c in Confidence], case_sensitive=False),
    required=True,
)
@click.option("--description", required=True, help="What was observed.")
@click.option("--recommendation", default=None, help="Suggested action.")
@click.option(
    "--source", "sources", multiple=True, help="Evidence source (repeatable)."
)
@click.option(
    "--source-url",
    "source_urls",
    multiple=True,
    help="Evidence URL (paired by position with --source).",
)
def finding_add(
    case_id: str,
    category: str,
    severity: str,
    confidence: str,
    description: str,
    recommendation: str | None,
    sources: tuple[str, ...],
    source_urls: tuple[str, ...],
) -> None:
    """Add a finding with optional evidence to a case."""
    source_list = list(sources)
    urls = list(source_urls)
    if len(urls) > len(source_list):
        raise click.ClickException("--source-url provided without a matching --source.")
    evidence = [
        Evidence(source=src, url=urls[i] if i < len(urls) else None)
        for i, src in enumerate(source_list)
    ]
    try:
        _, manager = _service()
        finding = manager.add_finding(
            case_id,
            Finding(
                category=category,
                severity=Severity(severity),
                confidence=Confidence(confidence),
                description=description,
                recommendation=recommendation,
                evidence=evidence,
            ),
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(f"Finding [bold]{finding.id}[/] ([{severity}] {category}) added.")


@finding_group.command("list")
@click.argument("case_id")
def finding_list(case_id: str) -> None:
    """List findings in a case."""
    try:
        _, manager = _service()
        findings = manager.list_findings(case_id)
        if not findings:
            console.print("[dim]No findings recorded.[/]")
            return
        console.print(_findings_table(findings))
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.group("relationship")
def relationship_group() -> None:
    """Manage identity relationships within a case."""


@relationship_group.command("add")
@click.argument("case_id")
@click.option("--from", "from_id", required=True, help="Identity A ID.")
@click.option("--to", "to_id", required=True, help="Identity B ID.")
@click.option(
    "--type",
    "relationship_type",
    required=True,
    help="Relationship type, e.g. same_username.",
)
@click.option(
    "--confidence",
    type=click.Choice([c.value for c in Confidence], case_sensitive=False),
    required=True,
)
@click.option("--notes", default=None, help="Optional context.")
@click.option(
    "--source", "sources", multiple=True, help="Evidence source (repeatable)."
)
def relationship_add(
    case_id: str,
    from_id: str,
    to_id: str,
    relationship_type: str,
    confidence: str,
    notes: str | None,
    sources: tuple[str, ...],
) -> None:
    """Add a relationship between two identities."""
    try:
        _, manager = _service()
        relationship = manager.add_relationship(
            case_id,
            Relationship(
                identity_a_id=from_id,
                identity_b_id=to_id,
                relationship_type=relationship_type,
                confidence=Confidence(confidence),
                notes=notes,
                evidence=[Evidence(source=s) for s in sources],
            ),
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(
        f"Relationship [bold]{relationship.id}[/] "
        f"({from_id} ↔ {to_id}, {relationship_type}) added."
    )


@relationship_group.command("list")
@click.argument("case_id")
def relationship_list(case_id: str) -> None:
    """List relationships in a case."""
    try:
        _, manager = _service()
        relationships = manager.list_relationships(case_id)
        if not relationships:
            console.print("[dim]No relationships recorded.[/]")
            return
        console.print(_relationships_table(relationships))
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command()
@click.argument("case_id")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "markdown"]),
    default=None,
    help="Report format (defaults to configured format).",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the report to a file instead of printing it.",
)
def report(case_id: str, fmt: str | None, output: Path | None) -> None:
    """Generate an assessment report for a case."""
    try:
        config, manager = _service()
        bundle = manager.build_bundle(case_id)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    format_ = fmt or config.default_report_format
    content = bundle.to_json() if format_ == "json" else bundle.to_markdown()

    if output is not None:
        output.write_text(content, encoding="utf-8")
        console.print(f"Report written to [bold]{output}[/].")
    else:
        console.print(content)


if __name__ == "__main__":
    cli()
