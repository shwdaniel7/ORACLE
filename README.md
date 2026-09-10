<p align="center">
  <img src="assets/logo.jpg" alt="ORACLE Logo" width="420" />
</p>

<h1 align="center">ORACLE</h1>

<p align="center"><strong>PERSONAL OPSEC INTELLIGENCE ENGINE</strong></p>

<p align="center"><em>OBSERVATION · INTELLIGENCE · ANALYSIS</em></p>

<p align="center"><em>Visibility is not the same as understanding.</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge" alt="Python" />
  <img src="https://img.shields.io/badge/Click-command_line_interface?style=for-the-badge&color=6b8e23" alt="Click" />
  <img src="https://img.shields.io/badge/Rich-silver?style=for-the-badge" alt="Rich" />
  <img src="https://img.shields.io/badge/Pydantic_v2-violet?style=for-the-badge" alt="Pydantic v2" />
  <img src="https://img.shields.io/badge/SQLAlchemy-red?style=for-the-badge" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/SQLite-044F88?style=for-the-badge" alt="SQLite" />
  <img src="https://img.shields.io/badge/JSON_%26_Markdown_Reports-4DB33D?style=for-the-badge" alt="JSON & Markdown Reports" />
  <img src="https://img.shields.io/badge/GPL--3.0-orange?style=for-the-badge" alt="GPL-3.0 License" />
  <img src="https://img.shields.io/badge/Windows-2374E1?style=for-the-badge" alt="Windows" />
</p>

<p align="center">
  <a href="https://github.com/shwdaniel7/ORACLE"><img src="https://img.shields.io/github/last-commit/shwdaniel7/ORACLE?style=for-the-badge" alt="Last Commit" /></a>
  <a href="https://github.com/shwdaniel7/ORACLE"><img src="https://img.shields.io/github/stars/shwdaniel7/ORACLE?style=for-the-badge" alt="Stars" /></a>
  <a href="https://github.com/shwdaniel7/ORACLE"><img src="https://img.shields.io/github/repo-size/shwdaniel7/ORACLE?style=for-the-badge" alt="Repository Size" /></a>
</p>

<p align="center"><sub><em>made by daniel • @shwdaniel7</em></sub></p>

---

## ⚠ Warning

ORACLE is a personal OPSEC (Operational Security) assessment tool. It evaluates how much of a digital identity is publicly discoverable, how apparently unrelated pieces of information can be correlated, and how that exposure can be reduced.

- Use ORACLE **only on your own digital footprint** or on information you are authorized to assess.
- It is not designed for profiling, targeting, or mass data collection about other people.
- A finding of `NOT_FOUND` never means something does not exist — it only means it was not observed.

---

## 📖 About

ORACLE approaches OPSEC as an **investigation problem**.

Modern digital identities are rarely contained within a single platform. A person may reuse the same username across many sites, reuse profile pictures, expose an email address in public repositories, leave metadata in uploaded files, or keep old accounts they no longer remember. Individually these pieces may seem harmless; together they can build a detailed picture of a person.

> **Exposure is often created through correlation rather than through a single piece of information.**

ORACLE exists to make that exposure visible. Instead of assuming what is private or public, you perform an assessment against your own digital footprint and understand where identities overlap, what information is exposed, and what should be addressed first.

The core question behind ORACLE:

> **"What could someone learn about me from the information I have left exposed?"**

Everything is stored locally. **Collect less. Expose less. Explain more.**

---

## 📐 The Four Stages

```text
DISCOVER
    ↓
CORRELATE
    ↓
ASSESS
    ↓
REMEDIATE
```

| Stage | Purpose | Status |
|---|---|---|
| **Discover** | Identify publicly accessible information associated with your identifiers (usernames, emails, domains, profiles). Public collectors are an upcoming roadmap phase. | 🔭 Planned |
| **Correlate** | Determine whether separate findings belong to the same digital identity, always with an explicit confidence level. | 🔭 Planned |
| **Assess** | Evaluate the OPSEC significance of each finding and produce an explainable exposure score. | ✅ Implemented |
| **Remediate** | Turn findings into an actionable, priority-ordered remediation plan. | ✅ Implemented |

The current release implements the **Assess** and **Remediate** stages on top of a local case model. Future phases add **Discover** (collectors) and **Correlate** (analyzers, identity graph).

---

## ✨ Capabilities

### Local case management

- create, list, show, and delete assessment cases, each representing one investigation
- register identifiers under a case: `username`, `email`, `domain`, `profile`, or `other`
- record findings with category, severity, confidence, description, evidence, and recommendation
- model identity correlations as relationships between identifiers, each with a confidence and supporting evidence

### Evidence-first findings

Every finding carries a structured context:

| Field | Meaning |
|---|---|
| `category` | What kind of exposure was observed |
| `severity` | `LOW` · `MEDIUM` · `HIGH` · `CRITICAL` |
| `confidence` | `CONFIRMED` · `POSSIBLE` · `INFERRED` · `NOT_FOUND` |
| `description` | What was observed |
| `evidence` | Where it was observed, with a source and optional URL |
| `recommendation` | A suggested action |

Uncertainty is never hidden. `NOT_FOUND` is explicitly not the same as "does not exist".

### Explainable OPSEC scoring

The assessment engine computes a transparent 0–100 score per dimension:

```text
Identity Separation
Username Hygiene
Email Exposure
Metadata Hygiene
Account Privacy
Public Information
Correlation Risk
```

Every score is derived from the findings that contributed to it, so the result is never an unexplained number.

### Remediation plans

Findings are grouped into a `HIGH` / `MEDIUM` / `LOW` priority plan of actionable recommendations, ready to be executed and re-assessed later.

### Structured reports

Assessments are exported as **JSON** (full structured data) or **Markdown** (readable audit), including executive summary, identity overview, exposure findings, correlations, scores, and remediation plan.

### Privacy-oriented design

Before collecting anything, ORACLE only stores what you give it, inside a local SQLite database under `~/.oracle/`. Report files warning about sensitive data, and future phases add EXIF removal, metadata sanitization, report encryption, and secure deletion.

---

## 📂 Project Structure

```
ORACLE/
├── LICENSE
├── README.md
├── pyproject.toml
├── assets/
│   └── logo.jpg
├── docs/
│   └── ORACLE_PROJECT_CONTEXT.md
└── oracle/
    ├── __init__.py
    ├── __main__.py
    ├── config.py            # TOML configuration loader
    ├── cli/                 # Click command-line interface
    │   └── main.py
    ├── models/              # Pydantic v2 domain models
    │   ├── case.py
    │   ├── evidence.py
    │   ├── finding.py
    │   ├── identity.py
    │   ├── relationship.py
    │   └── enums.py
    ├── database/            # SQLAlchemy persistence layer
    │   ├── engine.py
    │   ├── base.py
    │   └── orm_models.py
    ├── case/                # Local case management
    │   └── manager.py
    ├── collectors/          # Public information collectors (Phase 2)
    │   └── base.py          #   → BaseCollector contract
    ├── analyzers/           # Correlation analyzers (Phase 3)
    │   └── base.py          #   → BaseAnalyzer contract
    ├── opsec/               # Assessment engine
    │   ├── scoring.py
    │   └── recommendations.py
    ├── reports/             # Report generation
    │   └── generator.py
    └── tests/               # pytest suite
```

- `models/` holds the canonical Pydantic v2 data structures used everywhere.
- `database/` persists them with SQLAlchemy in a single local SQLite file.
- `case/manager.py` provides all CRUD operations for cases, identities, findings, and relationships.
- `opsec/scoring.py` and `opsec/recommendations.py` implement the assessment and remediation stages.
- `reports/generator.py` renders JSON and Markdown assessments.
- `cli/main.py` binds everything behind the `oracle` command.
- `collectors/` and `analyzers/` define the contracts for future discovery and correlation phases.

`docs/ORACLE_PROJECT_CONTEXT.md` is the full specification behind the project, including philosophy, architecture direction, visual identity, and roadmap.

---

## 🔄 Assessment Workflow

```text
oracle case new "My Audit"
       │
       ├─► identity add   → register your identifiers
       │
       ├─► finding add    → record evidence-based findings
       │
       ├─► relationship add → model identity correlations
       │
       ├─► report         → scoring + remediation plan
       │        │
       │        ├─► JSON assessment (full structured data)
       │        └─► Markdown assessment (readable audit)
       │
       └─► re-assess later → compare scores over time
```

Each case is an isolated investigation. Reports are generated from the case's stored identities, findings, relationships, computed scores, and remediation plan.

---

## 🚀 Installation

Requires **Python 3.10+**.

```bash
git clone https://github.com/shwdaniel7/ORACLE.git
cd ORACLE
pip install -e .
```

Command-line tool supported on Windows, macOS, and Linux.

---

## 🔑 Configuration

ORACLE reads a TOML file from `~/.oracle/config.toml` (overridable with the `ORACLE_CONFIG` environment variable):

```toml
[storage]
data_dir = "C:/Users/you/.oracle"

[reports]
default_format = "markdown"
```

Run `oracle init` to create the configuration and local storage automatically.

| Environment variable | Purpose |
|---|---|
| `ORACLE_CONFIG` | Path to the configuration file |
| `ORACLE_DATA_DIR` | Directory for the local SQLite database |

---

## 💻 Usage

```bash
oracle init
oracle case new "My First Audit"
oracle identity add <case-id> --type username --value "example_user"
oracle identity add <case-id> --type email --value "user@example.com"
oracle finding add <case-id> \
    --category "Identity Correlation" \
    --severity HIGH \
    --confidence CONFIRMED \
    --description "Same username observed across multiple platforms." \
    --source github.com --source reddit.com \
    --recommendation "Separate personal and public-facing identifiers."
oracle report <case-id> --format markdown
```

### Command reference

```text
oracle init                                    Initialize configuration and local storage
oracle case new <name> [--description]         Create an assessment case
oracle case list                               List all cases
oracle case show <case-id>                     Show case details and contents
oracle case delete <case-id> [--force]         Delete a case and all of its data
oracle identity add <case-id> --type <t> --value <v> [--label <l>]
oracle identity list <case-id>                 List identities in a case
oracle finding add <case-id> --category <c> --severity <s> --confidence <c> --description <d>
                  [--recommendation <r>] [--source <src> --source-url <url>]
oracle finding list <case-id>                  List findings in a case
oracle relationship add <case-id> --from <id-a> --to <id-b> --type <t> --confidence <c> [--notes]
oracle relationship list <case-id>             List relationships in a case
oracle report <case-id> --format json|markdown [--output <file>]
oracle version                                 Show the installed version
```

Run `oracle --help` for the full reference.

### Example interaction

```text
$ oracle version
ORACLE 0.1.0 — PERSONAL OPSEC INTELLIGENCE ENGINE

$ oracle case new "My Audit"

╭──────────────────────────────────────────────╮
│  Case created                                │
│  ID: 3de7ab8291004472bb92bff02be618b1        │
│  Name: My Audit                              │
╰──────────────────────────────────────────────╯
```

```text
$ oracle report <case-id> --format markdown
# ORACLE OPSEC ASSESSMENT

**PERSONAL OPSEC INTELLIGENCE ENGINE**

OBSERVATION · INTELLIGENCE · ANALYSIS

## Executive Summary

- **Case:** My Audit
- **Overall OPSEC Score:** 72 / 100

## Exposure Findings

### [HIGH · CONFIRMED] Identity Correlation

The same username is publicly associated with multiple identities.

**Evidence:**
- **github.com** (github.com)
- **reddit.com** (reddit.com)

**Recommendation:** Separate personal and public-facing identifiers.

## OPSEC Scores

| Dimension | Score |
|-----------|-------|
| Identity Separation | 58 |
| Username Hygiene | 41 |
| Correlation Risk | 55 |
| **Overall** | **72** |

## Remediation Plan

### HIGH PRIORITY

- [ ] Replace reused username on personal accounts
```

Reports can also be written to disk:

```bash
oracle report <case-id> --format json --output report.json
oracle report <case-id> --format markdown --output report.md
```

---

## 🧩 Architecture

### `oracle/models/`

Pydantic v2 domain models: `Case`, `Identity`, `Finding`, `Evidence`, and `Relationship`, plus the shared `Severity` and `Confidence` enums. These models are the single source of truth used by the CLI, the database, and the reports.

### `oracle/database/`

SQLAlchemy 2.0 persistence over a single local SQLite file. Case data is fully isolated per case, and any relationship or finding can carry supporting evidence.

### `oracle/case/manager.py`

The `CaseManager` is the core service: it creates cases, registers identities, stores findings with evidence, models relationships, and assembles a full assessment bundle for reporting. Every method works against the local database with no network access.

### `oracle/opsec/`

- `scoring.py` — maps findings to the seven assessment dimensions and produces an explainable 0–100 score. Confidence weights modulate the penalty of each finding (`CONFIRMED` full weight, `INFERRED`/`POSSIBLE` reduced, `NOT_FOUND` none).
- `recommendations.py` — converts findings into a `HIGH` / `MEDIUM` / `LOW` remediation plan.

### `oracle/reports/generator.py`

Renders an `AssessmentBundle` — case, identities, findings, relationships, scores, and remediation — into JSON (structured) or Markdown (readable). The Markdown report contains executive summary, identity overview, exposure findings with evidence, correlations, the OPSEC score table, and the remediation plan.

### `oracle/cli/main.py`

A Click group with Rich output styled in ORACLE's olive green, exposing `init`, `case`, `identity`, `finding`, `relationship`, `report`, and `version`.

### Contracts for future phases

- `collectors/base.py` defines `BaseCollector`, the contract for Phase 2 public information discovery.
- `analyzers/base.py` defines `BaseAnalyzer`, the contract for Phase 3 correlation analysis.

Both are intentionally empty skeletons so future engines plug in without changing the CLI or the models.

---

## 🔬 Technical Concepts

### Confidence, not certainty

Every finding and relationship carries an explicit confidence state:

```text
CONFIRMED    Observed with direct evidence
POSSIBLE     Plausible but not fully verified
INFERRED     Derived from context
NOT_FOUND    Not observed
```

ORACLE never turns a possibility into a fact merely because it looks plausible.

### Context before risk

A single public username is not automatically dangerous. ORACLE evaluates findings in context — the same username on a personal forum, combined with a personal email and location information, becomes a meaningful correlation. Findings are scored and prioritized together rather than treated as isolated facts.

### Explainable scoring

The overall score is the mean of the seven dimension scores, and each dimension is the sum of severity-weighted penalties from its contributing findings. No score exists without the findings behind it.

### Local first, data minimization

Analysis and storage are entirely local. ORACLE does not collect or retain information without a reason, and the user owns the investigation and its results.

---

## 🛣 Roadmap

```text
Phase 1 · Foundation        ✅ Current release  → CLI, config, cases, models, scoring, reporting
Phase 2 · Exposure Discovery  🔭  → username / email / domain / profile collectors
Phase 3 · Identity Correlation 🔭  → identity graph, confidence scoring, relationship evidence
Phase 4 · OPSEC Assessment  🔭  → risk categories, finding prioritization
Phase 5 · Privacy Tools     🔭  → EXIF analysis, metadata sanitization, encrypted reports
Phase 6 · GUI               🔭  → dashboard, graph visualization, findings interface
Phase 7 · Historical Intelligence 🔭 → assessment history, exposure comparison, trends
```

---

## 🤝 Relationship to CERBERUS

ORACLE and [CERBERUS](https://github.com/shwdaniel7/CERBERUS) are separate tools that share a common design philosophy:

```text
CERBERUS
    ↓
Looks inside the artifact.

ORACLE
    ↓
Looks outward at the identity.
```

| | CERBERUS | ORACLE |
|---|---|---|
| **Subtitle** | STATIC MALWARE ANALYSIS ENGINE | PERSONAL OPSEC INTELLIGENCE ENGINE |
| **Color** | Red | Olive Green |
| **Focus** | Files · Malware · Indicators · Static Analysis · Evidence | Identity · Exposure · Correlation · Privacy · OPSEC |

Both projects favor: **Evidence first. Context before conclusions.**

---

## 📚 Technologies

- Python 3.10+
- Click (command-line interface)
- Rich (terminal output)
- Pydantic v2 (domain models and validation)
- SQLAlchemy 2.0 (SQLite persistence)
- TOML (configuration)
- JSON / Markdown (report generation)

---

## ⚖ Legal Notice

ORACLE is a defensive, personal-security tool. It is intended for self-assessment of your own digital footprint and is designed around publicly accessible information, user-provided information, legitimate APIs, and local analysis.

ORACLE must not be used for credential theft, unauthorized account access, mass targeting of individuals, or covert surveillance.

The author assumes no responsibility for misuse. Use this project only on information you are permitted to assess.

---

## 📄 License

GNU General Public License v3.0 or later. See [LICENSE](LICENSE).