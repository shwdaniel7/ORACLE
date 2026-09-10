# ORACLE --- Project Context

**PERSONAL OPSEC INTELLIGENCE ENGINE**

> **OBSERVATION · INTELLIGENCE · ANALYSIS**

------------------------------------------------------------------------

## 1. Project Overview

ORACLE is a personal Operational Security (OPSEC) and digital exposure
assessment tool designed to help individuals understand what information
about them is publicly discoverable, how apparently unrelated pieces of
information can be correlated, and how their digital footprint can be
reduced.

The project approaches OPSEC as an **investigation problem**.

Rather than simply checking whether a username, email address, or
profile exists somewhere online, ORACLE attempts to build a contextual
view of a user's digital presence and identify relationships between
publicly available information.

The core question behind ORACLE is:

> **"What could someone learn about me from the information I have left
> exposed?"**

ORACLE is intended to answer that question with evidence, context, risk
assessment, and actionable recommendations.

------------------------------------------------------------------------

## 2. Motivation

Modern digital identities are rarely contained within a single platform.

A person may use the same username across several websites, reuse
profile pictures, expose an email address in public repositories, leave
metadata in uploaded files, or maintain old accounts that they no longer
remember.

Individually, these pieces of information may appear harmless.

Together, they can create a detailed picture of a person.

This creates an important OPSEC problem:

> **Exposure is often created through correlation rather than through a
> single piece of information.**

ORACLE exists to make that exposure visible.

Instead of relying on assumptions about what is private or public, the
user can perform an assessment against their own digital footprint and
understand where identities overlap, what information is exposed, and
which issues should be addressed first.

------------------------------------------------------------------------

## 3. Core Concept

ORACLE is built around four stages:

``` text
DISCOVER
    ↓
CORRELATE
    ↓
ASSESS
    ↓
REMEDIATE
```

### Discover

Identify publicly accessible information associated with the user's
provided identifiers.

Examples include:

-   usernames;
-   email addresses;
-   domains;
-   public profiles;
-   public repositories;
-   images and metadata;
-   other relevant digital identifiers.

### Correlate

Determine whether individual findings may belong to the same digital
identity.

Examples:

``` text
username
    ↓
public profile
    ↓
same avatar
    ↓
same email
    ↓
same identity
```

Correlation must distinguish between verified relationships and
uncertain relationships.

### Assess

Evaluate the potential OPSEC significance of each finding.

ORACLE should consider factors such as:

-   sensitivity;
-   uniqueness;
-   public accessibility;
-   identity linkage;
-   historical persistence;
-   potential for further correlation;
-   potential consequences.

### Remediate

Provide practical recommendations for reducing unnecessary exposure.

The goal is not merely to identify problems, but to help the user
understand how to address them.

------------------------------------------------------------------------

## 4. Project Philosophy

### Evidence Before Conclusions

ORACLE must prioritize evidence over assumptions.

Every finding should make it possible to understand:

-   what was found;
-   where it was found;
-   when it was observed, when applicable;
-   why it may matter;
-   how confident ORACLE is in the finding.

The system should avoid presenting uncertain correlations as facts.

Findings should therefore use explicit confidence states such as:

``` text
CONFIRMED
POSSIBLE
INFERRED
NOT FOUND
```

"Not found" must never be interpreted as "does not exist."

------------------------------------------------------------------------

### Context Before Risk

The existence of information does not automatically make it dangerous.

For example:

``` text
Public username
```

may be relatively insignificant by itself.

However:

``` text
Public username
    +
same username on personal forum
    +
personal email
    +
location information
```

may represent a meaningful identity correlation.

ORACLE should therefore evaluate findings in context rather than
treating every discovery as equally important.

------------------------------------------------------------------------

### User-Owned Investigation

ORACLE is primarily intended for **self-assessment**.

The central use case is:

> **Investigate your own digital footprint to improve your own OPSEC.**

The project should not be designed around profiling, targeting, or
collecting sensitive information about unrelated individuals.

This principle should influence both the user experience and the
architecture of the application.

------------------------------------------------------------------------

### Minimize the Investigator

A security tool that creates unnecessary sensitive data about its own
user defeats part of its purpose.

ORACLE should therefore follow a **data minimization** philosophy.

Whenever practical:

-   perform analysis locally;
-   avoid unnecessary persistence of collected information;
-   clearly communicate what data is being processed;
-   avoid collecting information that is not required for the
    assessment;
-   provide users with control over generated reports and stored cases.

The tool should help the user improve their OPSEC without becoming
another source of exposure.

------------------------------------------------------------------------

## 5. Primary Use Cases

### Personal Digital Footprint Audit

A user provides identifiers they commonly use online.

ORACLE evaluates their public exposure and produces an assessment.

``` text
Username
Email
Domain
Public profiles
Images
```

------------------------------------------------------------------------

### Username Reuse Assessment

Determine where a username appears across supported public services and
identify potential reuse.

Example:

``` text
USERNAME: example_user

GitHub       CONFIRMED
Reddit       CONFIRMED
Forum        CONFIRMED
YouTube      POSSIBLE
Instagram    NOT FOUND
```

The result should also evaluate whether reuse creates an identity
correlation risk.

------------------------------------------------------------------------

### Identity Correlation

Identify potential relationships between apparently separate accounts.

Possible correlation signals include:

-   identical usernames;
-   similar usernames;
-   reused profile images;
-   public email addresses;
-   linked websites;
-   consistent biographies;
-   shared domains;
-   other publicly observable identifiers.

Correlation should always include a confidence level.

------------------------------------------------------------------------

### Email Exposure Assessment

Determine where a public email address appears and whether it connects
multiple digital identities.

ORACLE should distinguish between:

``` text
Publicly exposed
Previously exposed
Potentially associated
Not found
```

Where appropriate, the tool may also provide guidance for separating
personal, professional, and public-facing identities.

------------------------------------------------------------------------

### Image OPSEC Audit

Analyze user-provided images for potentially sensitive metadata.

Possible findings include:

-   GPS coordinates;
-   timestamps;
-   camera information;
-   software information;
-   device information;
-   other EXIF metadata.

The user should be able to create a sanitized copy of an image with
unnecessary metadata removed.

------------------------------------------------------------------------

### Public Information Assessment

Identify information that may contribute to a broader picture of the
user's identity.

Examples:

-   approximate location;
-   professional information;
-   personal websites;
-   old profiles;
-   public contact information;
-   usernames;
-   associated domains.

ORACLE should focus on **exposure and correlation**, not simply
quantity.

------------------------------------------------------------------------

## 6. OPSEC Assessment Model

ORACLE may provide an overall OPSEC assessment, but the score must
remain explainable.

A possible model is:

``` text
Identity Separation
Username Hygiene
Email Exposure
Account Privacy
Metadata Hygiene
Public Information
Correlation Risk
Credential Security Awareness
```

Example:

``` text
ORACLE OPSEC ASSESSMENT

Overall: 72 / 100

Identity Separation       58
Username Hygiene          41
Email Exposure            82
Metadata Hygiene          91
Account Privacy           74
Public Information        67
Correlation Risk          55
```

The score should never be treated as an objective measure of someone's
absolute security.

It is an **assessment aid** intended to prioritize remediation.

Every score should be accompanied by the findings that contributed to
it.

------------------------------------------------------------------------

## 7. Exposure Findings

Each finding should contain structured information similar to:

``` text
Finding
────────────────────────────
Category: Identity Correlation
Severity: HIGH
Confidence: CONFIRMED

Description:
The same username is publicly associated
with multiple identities.

Evidence:
- Source A
- Source B
- Source C

Potential Impact:
These accounts may be correlated by a third party.

Recommendation:
Separate identifiers between personal and
public-facing identities.
```

This makes the output useful for both humans and future automation.

------------------------------------------------------------------------

## 8. Remediation

ORACLE should turn findings into an actionable remediation plan.

Example:

``` text
REMEDIATION PLAN

HIGH PRIORITY

[ ] Replace reused username on personal accounts
[ ] Remove personal email from public repository
[ ] Review old public profile
[ ] Sanitize image metadata

MEDIUM PRIORITY

[ ] Review account privacy settings
[ ] Separate personal and professional identities
[ ] Audit inactive accounts
```

After remediation, the user should be able to perform another assessment
and compare results.

``` text
Previous Assessment
    ↓
Remediation
    ↓
New Assessment
    ↓
Exposure Reduced
```

------------------------------------------------------------------------

## 9. Identity Graph

One of ORACLE's central concepts is the **Identity Graph**.

Instead of representing findings as an isolated list, ORACLE may
represent relationships as a graph:

``` text
                    User
                     │
          ┌──────────┼──────────┐
          │          │          │
       Username    Email      Domain
          │          │          │
       GitHub      Forum      Website
          │          │
        Avatar ──────┘
```

Nodes represent entities or identifiers.

Edges represent relationships.

Each relationship should contain a confidence value and, where possible,
supporting evidence.

This graph can become the foundation for more advanced correlation
analysis.

------------------------------------------------------------------------

## 10. Exposure Timeline

Digital exposure can change over time.

ORACLE should eventually support historical assessments:

``` text
2026-09-10
Exposure Score: 61

2026-10-15
Exposure Score: 48

2026-12-03
Exposure Score: 32
```

This allows the user to determine whether remediation efforts actually
reduced their public exposure.

------------------------------------------------------------------------

## 11. Privacy-Oriented Features

ORACLE may eventually provide local utilities for reducing exposure.

Potential features include:

-   EXIF removal;
-   metadata sanitization;
-   report encryption;
-   local case storage;
-   sensitive-data redaction;
-   export controls;
-   secure deletion of locally generated assessment data.

These features should follow the same principle as the rest of the
project:

> **Collect less. Expose less. Explain more.**

------------------------------------------------------------------------

## 12. Architecture Direction

ORACLE should be designed as a modular Python application.

A conceptual structure may resemble:

``` text
oracle/
│
├── collectors/
│   ├── username.py
│   ├── email.py
│   ├── domain.py
│   └── web.py
│
├── analyzers/
│   ├── identity.py
│   ├── correlation.py
│   ├── exposure.py
│   └── metadata.py
│
├── opsec/
│   ├── scoring.py
│   ├── findings.py
│   └── recommendations.py
│
├── privacy/
│   ├── metadata_cleaner.py
│   └── sanitization.py
│
├── reports/
│   └── generator.py
│
├── cli/
│
├── gui/
│
└── tests/
```

The exact architecture may change during development.

The important principle is separation of concerns between:

``` text
Collection
Analysis
Correlation
Assessment
Remediation
Presentation
```

------------------------------------------------------------------------

## 13. CLI and GUI

ORACLE should eventually provide both a CLI and a graphical interface.

### CLI

The CLI should be useful for:

-   automation;
-   scripting;
-   repeatable assessments;
-   technical users;
-   structured exports.

Example:

``` text
oracle scan username example_user
oracle scan email user@example.com
oracle audit image photo.jpg
oracle report case-001
```

### GUI

The GUI should prioritize investigation and comprehension.

Potential sections:

``` text
Dashboard
Identity
Exposure
Correlations
Findings
Timeline
Remediation
Reports
Settings
```

The interface should make complex relationships understandable without
hiding the underlying evidence.

------------------------------------------------------------------------

## 14. Reporting

ORACLE should support structured reports suitable for personal security
audits.

A report may contain:

``` text
Executive Summary
Identity Overview
Exposure Findings
Identity Correlations
Metadata Findings
Risk Assessment
Recommended Actions
Evidence
Assessment Timestamp
```

Potential output formats:

-   JSON;
-   Markdown;
-   HTML;
-   PDF.

Reports should avoid unnecessarily reproducing sensitive information and
should provide appropriate warnings when exporting potentially sensitive
data.

------------------------------------------------------------------------

## 15. Security Boundaries

ORACLE is intended for defensive and personal security use.

The project should prioritize:

-   publicly accessible information;
-   user-provided information;
-   legitimate APIs;
-   permitted data sources;
-   local analysis.

ORACLE should not be designed around:

-   credential theft;
-   unauthorized account access;
-   bypassing authentication;
-   exploiting private systems;
-   mass targeting of individuals;
-   acquiring restricted personal information;
-   covert surveillance.

The project should remain an **OPSEC assessment and privacy tool**, not
an offensive intelligence platform.

------------------------------------------------------------------------

## 16. Technology Direction

Python is the primary implementation language.

Potential technologies may include:

-   Python;
-   SQLite;
-   HTTP clients;
-   HTML parsing;
-   public APIs;
-   EXIF/metadata libraries;
-   graph-oriented data structures;
-   Tkinter or another Python-compatible GUI framework;
-   JSON/Markdown/HTML report generation.

Dependencies should be introduced only when they provide meaningful
functionality.

The project should favor understandable, maintainable components over
unnecessary complexity.

------------------------------------------------------------------------

## 17. Visual Identity

ORACLE is part of a broader collection of personal cybersecurity tools.

Each project should have its own distinct visual identity while
maintaining a consistent technical character.

### Primary Identity

**ORACLE**

### Official Subtitle

**PERSONAL OPSEC INTELLIGENCE ENGINE**

### Secondary Brand Line

**OBSERVATION · INTELLIGENCE · ANALYSIS**

The subtitle defines the function of the software.

The secondary brand line represents the conceptual identity of ORACLE
and may be used across visual assets, splash screens, promotional
material, documentation, and other branding elements.

------------------------------------------------------------------------

### Primary Color

**Olive Green**

ORACLE uses a muted olive green as its signature color.

The chosen direction intentionally avoids highly saturated neon green.

The color should communicate:

-   observation;
-   intelligence;
-   analysis;
-   technology;
-   controlled visibility.

It should also distinguish ORACLE from other tools in the project
collection.

The exact production color value should be defined as part of the final
design system.

------------------------------------------------------------------------

### Symbol

The ORACLE symbol is based on an **abstract alien spacecraft**.

The spacecraft represents observation and intelligence while subtly
referencing the Oracle codename associated with Futaba Sakura in
*Persona 5*.

The reference should remain indirect.

The visual identity must function independently from the source material
and should not rely on depicting the character itself.

The symbol combines the conceptual language of:

-   an alien spacecraft;
-   an eye;
-   a radar;
-   a lens;
-   an observation instrument.

The central element represents the act of observing, while the
surrounding structure suggests scanning, perception, and connected
information.

The final symbol should remain minimal, geometric, and recognizable at
small sizes.

------------------------------------------------------------------------

## 18. Design Language

ORACLE should feel:

-   technical;
-   intelligent;
-   investigative;
-   modern;
-   restrained;
-   slightly mysterious.

It should avoid:

-   generic hacker imagery;
-   excessive glitch effects;
-   stereotypical green terminal screens;
-   unnecessary cyberpunk decoration;
-   exaggerated neon;
-   character artwork as the primary identity.

The aesthetic should communicate **intelligence and observation**,
rather than aggression.

------------------------------------------------------------------------

## 19. Relationship to CERBERUS

ORACLE and CERBERUS are separate tools with different purposes, but they
share a common design philosophy.

### CERBERUS

``` text
STATIC MALWARE ANALYSIS ENGINE

Color:
Red

Focus:
Files
Malware
Indicators
Static Analysis
Evidence
```

### ORACLE

``` text
PERSONAL OPSEC INTELLIGENCE ENGINE

Color:
Olive Green

Focus:
Identity
Exposure
Correlation
Privacy
OPSEC
```

Conceptually:

``` text
CERBERUS
    ↓
Looks inside the artifact.

ORACLE
    ↓
Looks outward at the identity.
```

Both projects should favor:

> **Evidence first. Context before conclusions.**

Each tool should have its own symbolic identity and signature color
while remaining recognizable as part of the same broader cybersecurity
portfolio.

------------------------------------------------------------------------

## 20. Development Principles

ORACLE should follow these principles throughout development:

### 1. Evidence First

Every meaningful finding should have an understandable basis.

### 2. Explainability

The user should understand why ORACLE considers something relevant.

### 3. Confidence Awareness

Uncertainty must be explicitly represented.

### 4. Data Minimization

Do not collect or retain information without a reason.

### 5. Local First

Whenever practical, analysis should happen locally.

### 6. User Control

The user owns the investigation and its results.

### 7. Actionable Results

Findings should lead to useful recommendations.

### 8. Modular Architecture

Collectors, analyzers, correlation logic, scoring, and presentation
should remain separable.

### 9. Repeatability

Assessments should be reproducible and comparable over time.

### 10. No False Certainty

ORACLE should never turn a possibility into a fact merely because it
looks plausible.

------------------------------------------------------------------------

## 21. Initial Roadmap

### Phase 1 --- Foundation

-   [ ] Project structure
-   [ ] CLI foundation
-   [ ] Configuration system
-   [ ] Local case management
-   [ ] Finding model
-   [ ] Evidence model
-   [ ] Basic reporting

### Phase 2 --- Exposure Discovery

-   [ ] Username assessment
-   [ ] Email assessment
-   [ ] Domain assessment
-   [ ] Public profile discovery
-   [ ] Basic source management

### Phase 3 --- Identity Correlation

-   [ ] Identity graph
-   [ ] Username correlation
-   [ ] Profile-image correlation
-   [ ] Email correlation
-   [ ] Confidence scoring
-   [ ] Relationship evidence

### Phase 4 --- OPSEC Assessment

-   [ ] Exposure scoring
-   [ ] Risk categories
-   [ ] Finding prioritization
-   [ ] OPSEC recommendations
-   [ ] Remediation plans

### Phase 5 --- Privacy Tools

-   [ ] EXIF analysis
-   [ ] Metadata sanitization
-   [ ] Sensitive-data detection
-   [ ] Local report protection

### Phase 6 --- GUI

-   [ ] Dashboard
-   [ ] Identity graph visualization
-   [ ] Findings interface
-   [ ] Exposure timeline
-   [ ] Remediation tracking
-   [ ] Report generation

### Phase 7 --- Historical Intelligence

-   [ ] Assessment history
-   [ ] Exposure comparison
-   [ ] Remediation tracking
-   [ ] Long-term exposure trends

------------------------------------------------------------------------

## 22. Long-Term Vision

The long-term goal of ORACLE is not to become the largest OSINT
collection tool.

Its goal is to become a **personal digital exposure intelligence
platform**.

A user should be able to sit down, provide the identities and
information they knowingly use online, run an assessment, and receive an
understandable representation of:

``` text
WHAT IS PUBLIC
       ↓
WHAT IS CONNECTED
       ↓
WHAT MATTERS
       ↓
WHAT SHOULD CHANGE
```

The ideal outcome is not more information.

It is **better control over the information that already exists**.

------------------------------------------------------------------------

## 23. Project Identity Statement

> **ORACLE is a Personal OPSEC Intelligence Engine that helps users
> discover, understand, and reduce their digital exposure.**

Its purpose is simple:

> **See what the world can see. Understand how it connects. Decide what
> should remain visible.**

------------------------------------------------------------------------

## 24. Brand Statement

``` text
ORACLE
PERSONAL OPSEC INTELLIGENCE ENGINE

OBSERVATION · INTELLIGENCE · ANALYSIS
```

The visual identity represents a system that observes the digital
environment, interprets relationships between exposed information, and
transforms those observations into intelligence that the user can act
upon.

The spacecraft symbolizes the act of observing from outside the system.

The eye-like central element represents perception.

The network-like structure represents the relationships between digital
identities.

Together, they represent the core idea of ORACLE:

> **Observe the footprint. Understand the connections. Take back
> control.**

------------------------------------------------------------------------

## 25. Guiding Principle

``` text
             ┌───────────────┐
             │    ORACLE     │
             │               │
             │   OBSERVE     │
             │       ↓       │
             │   CORRELATE   │
             │       ↓       │
             │    ASSESS     │
             │       ↓       │
             │   REMEDIATE   │
             └───────────────┘
```

**Visibility is not the same as understanding.**

ORACLE exists to bridge that gap.
