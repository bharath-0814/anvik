# Anvik

> **PS 16 — UPI Fraud-Ring Graph Investigator with Explainable Alerts**  
> *Code-e-Manipal Hackathon Project*

[![Live Demo](https://img.shields.io/badge/Live%20Platform-anvik--frontend--alpha.vercel.app-0A7347?style=for-the-badge&logo=vercel)](https://anvik-frontend-alpha.vercel.app)
[![API Swagger Docs](https://img.shields.io/badge/API%20Docs-Swagger%20%2F%20OpenAPI-0284C7?style=for-the-badge&logo=fastapi)](https://anvik-backend.vercel.app/docs)
[![API ReDoc](https://img.shields.io/badge/API%20Specs-ReDoc-6366F1?style=for-the-badge&logo=openapiinitiative)](https://anvik-backend.vercel.app/redoc)
[![Backend Status](https://img.shields.io/badge/Backend%20API-Online%20(Vercel)-007065?style=for-the-badge&logo=fastapi)](https://anvik-backend.vercel.app/health)
[![Database](https://img.shields.io/badge/Database-Turso%20libSQL-4FF8D2?style=for-the-badge&logo=sqlite&logoColor=black)](https://anvik-backend.vercel.app/ready)
[![CI Status](https://img.shields.io/badge/CI-Automated%20Tests%20Passing-success?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/bharath-0814/anvik/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![GitHub Monorepo](https://img.shields.io/badge/GitHub-bharath--0814%2Fanvik-181717?style=for-the-badge&logo=github)](https://github.com/bharath-0814/anvik)

---

## 🌐 Live Deployments & Working Links

For hackathon judges, evaluators, and contributors, all production deployments and API endpoints are actively hosted, verified, and accessible via the working links below:

| Resource / Endpoint | Live Working Link | Description & Health Check |
|---|---|---|
| **Live Web Platform** | [anvik-frontend-alpha.vercel.app](https://anvik-frontend-alpha.vercel.app) | Production interactive single-page app with Cytoscape.js topologies, dynamic timelines, and case management |
| **Live FastAPI Backend** | [anvik-backend.vercel.app](https://anvik-backend.vercel.app) | High-performance FastAPI backend service hosted on Vercel Serverless |
| **Interactive Swagger UI** | [anvik-backend.vercel.app/docs](https://anvik-backend.vercel.app/docs) | Interactive OpenAPI exploration tool for executing queries and inspecting schemas |
| **Interactive ReDoc** | [anvik-backend.vercel.app/redoc](https://anvik-backend.vercel.app/redoc) | Human-readable API documentation generated directly from OpenAPI contracts |
| **Service Liveness Probe** | [anvik-backend.vercel.app/health](https://anvik-backend.vercel.app/health) | Zero-dependency liveness check (`GET /health`) returning `{"status":"healthy"}` |
| **Database Readiness Probe** | [anvik-backend.vercel.app/ready](https://anvik-backend.vercel.app/ready) | Verifies active Turso libSQL cloud connectivity (`GET /ready`) |
| **Live Fraud Alerts API** | [anvik-backend.vercel.app/api/alerts](https://anvik-backend.vercel.app/api/alerts) | 24 evidence-linked alerts with scoring breakdown, focal accounts, and counterfactuals |
| **Live Graph Topology API** | [anvik-backend.vercel.app/api/graph](https://anvik-backend.vercel.app/api/graph) | Directed multigraph endpoint returning Cytoscape-compliant node and edge models |
| **Live NCRP Complaints API** | [anvik-backend.vercel.app/api/complaints](https://anvik-backend.vercel.app/api/complaints) | Searchable NCRP cybercrime portal complaints mapped to transaction networks |
| **Main Monorepo (GitHub)** | [github.com/bharath-0814/anvik](https://github.com/bharath-0814/anvik) | Canonical monorepo containing full backend, frontend, detection engine, and test suites |
| **Standalone Frontend (GitHub)** | [github.com/bharath-0814/anvik-frontend](https://github.com/bharath-0814/anvik-frontend) | Dedicated frontend repository synchronised with production Vercel builds |
| **Upstream UI Prototype (GitHub)** | [github.com/Kbharti-25/avnikfrontend](https://github.com/Kbharti-25/avnikfrontend) | Upstream UI prototyping repository created by Piyush |

---

## 📑 Table of Contents

- [1. Project Identity and Objective](#1-project-identity-and-objective)
- [2. System Architecture](#2-system-architecture)
- [3. Key Investigative Capabilities](#3-key-investigative-capabilities)
- [4. Rule-Based Detection Engine](#4-rule-based-detection-engine)
- [5. Synthetic Benchmark Datasets](#5-synthetic-benchmark-datasets)
- [6. Technology Stack](#6-technology-stack)
- [7. Local Development & Quickstart](#7-local-development--quickstart)
- [8. Team Ownership & Responsibilities](#8-team-ownership--responsibilities)
- [9. Technical Documentation & Specifications](#9-technical-documentation--specifications)
- [10. Compliance & Ethical Disclaimers](#10-compliance--ethical-disclaimers)

---

## 1. Project Identity and Objective

**Anvik** is an investigative decision-support system built for financial intelligence analysts, cybercrime units, and compliance officers to rapidly identify, trace, and dismantle coordinated UPI mule networks and fraud rings.

Modern UPI fraud schemes exploit multi-layered money dispersion, rapid pass-through chains (seconds to minutes), circular funds layering, and device collusion farms. Anvik models multi-party synthetic financial records as a directed multigraph, executing deterministic pattern-detection rules to generate explainable, evidence-backed priority alerts.

> [!IMPORTANT]
> **Investigative Decision Support Only**: Anvik is an analytical aid for investigators, not an automated system for declaring individuals guilty. Suspicious alerts, graph anomalies, and shared identifiers represent investigative leads for human verification, not conclusive proof of guilt.

> [!NOTE]
> **Synthetic Data Policy**: Anvik exclusively operates on synthetic transaction datasets. It never connects to live banking infrastructure, live UPI switches, payment gateways, or real personal financial credentials.

---

## 2. System Architecture

Anvik couples an interactive, responsive React frontend with a modular Python/FastAPI graph detection engine and hosted Turso libSQL database:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ANVIK SYSTEM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │                 React 18 / TypeScript Frontend UI                   │
  │     (Interactive Cytoscape.js Topologies, SVG Playback Canvas,      │
  │        Evidence Rail, NCRP Intake, and Audit Report Generator)      │
  │             Live: https://anvik-frontend-alpha.vercel.app            │
  └──────────────────┬───────────────────────────────▲──────────────────┘
                     │                               │
             REST API Requests               JSON Graph & Alerts
             (CORS-enabled)                  (Cytoscape format)
                     │                               │
  ┌──────────────────▼───────────────────────────────┴──────────────────┐
  │                   Python 3.11+ FastAPI Backend                      │
  │         (Routers: /api/graph, /api/alerts, /api/complaints)         │
  │              Live: https://anvik-backend.vercel.app                 │
  └──────────────┬───────────────────────────────┬──────────────────────┘
                 │                               │
         NetworkX Directed                SQLAlchemy / libSQL
            Multigraph                       Client Query
                 │                               │
  ┌──────────────▼──────────────┐ ┌──────────────▼──────────────────────┐
  │  Fraud Detection Engine     │ │      Turso libSQL Database          │
  │  - Rapid Onward Transfer    │ │  (Accounts, Devices, Transactions,  │
  │  - Multi-Source Fan-In      │ │   Merchants, Complaints Tables)     │
  │  - Fan-Out Layering         │ │                                     │
  │  - Circular Loop Detection  │ │  Hosted: libSQL over WebSocket      │
  │  - Device Collusion Rings   │ │  Local Fallback: In-memory SQLite   │
  └─────────────────────────────┘ └─────────────────────────────────────┘
```

---

## 3. Key Investigative Capabilities

- **Interactive Cytoscape.js Topologies**: Explore interconnected accounts, devices, and transactions with smooth physics simulation (`cose`), concentric ring layers, and adaptive zoom/pan controls.
- **Focused 5-Node Core Chain**: Instantly declutter complex syndicates down to executive, decision-ready 5-node subgraphs (`Victim → Aggregator → Collector`).
- **Evidence-Linked Priority Scoring**: Explainable mathematical suspicion scoring (0.00 – 1.00) based on forwarding ratios, hop counts, time deltas, and multi-source dispersion.
- **Chronological Transaction Timelines**: Interactive time-scrubber and playback bar to visualize funds dispersion step-by-step.
- **NCRP Cybercrime Complaint Convergence**: Trace victim dispute filings directly to secondary mules and cash-out points.
- **Counterfactual Fragility Analysis**: Evaluate syndicate resilience by simulating entity freezing (`What if Account X is blocked?`).
- **Forensic Case Report Generator**: One-click downloadable audit reports with formatted evidence tables, risk scoring, and counterparty breakdown.

---

## 4. Rule-Based Detection Engine

Anvik implements 8 deterministic, transparent fraud detection algorithms operating over directed transaction multigraphs:

| Rule Identifier | Rule Name | Detection Methodology & Thresholds |
|---|---|---|
| `RAPID_ONWARD_TRANSFER` | Rapid Onward Transfer | Detects accounts forwarding $\ge 80\%$ of received funds to downstream counterparties within $\le 30$ minutes. |
| `MULTI_SOURCE_FAN_IN` | Multi-Source Fan-In | Flags aggregator mule accounts receiving deposits from $\ge 3$ distinct origin accounts within a 120-minute window. |
| `FAN_OUT_SPLITTING` | Fan-Out Layering | Identifies structuring accounts receiving a lump-sum deposit and rapidly splitting it into $\ge 3$ smaller outbound transfers. |
| `TRANSACTION_CYCLE` | Circular Funds Layering | Detects closed directed cycles ($A \to B \to C \to A$) within a 24-hour window exhibiting $\ge 90\%$ amount retention. |
| `COMPLAINT_CONVERGENCE` | Complaint Convergence | Traces funds originating from $\ge 2$ independent NCRP victim complaints converging into a shared beneficiary. |
| `NEW_ACCOUNT_BURST` | New Account Burst Velocity | Flags recently activated accounts exhibiting sudden high-velocity volume spikes far exceeding baseline activity. |
| `COLLECT_REQUEST_ABUSE` | Collect Request Fraud | Detects repeated deceptive UPI collect requests followed by immediate outbound fund dispersion. |
| `SHARED_DEVICE` | Shared Device Collusion | Identifies device hardware fingerprints linked to $\ge 3$ distinct bank accounts across different institutions. |

---

## 5. Synthetic Benchmark Datasets

Anvik includes comprehensive, validated synthetic datasets containing ground-truth fraud ring scenarios alongside realistic benign control transactions:

| Dataset File | Link | Description |
|---|---|---|
| `accounts.csv` | [backend/data/accounts.csv](backend/data/accounts.csv) | 200 synthetic accounts spanning SBI, HDFC, ICICI, Axis, and Paytm |
| `transactions.csv` | [backend/data/transactions.csv](backend/data/transactions.csv) | 3,300+ synthetic transactions spanning PAY and COLLECT flows with timestamps |
| `devices.csv` | [backend/data/devices.csv](backend/data/devices.csv) | Device hardware IDs, OS versions, IP mappings, and shared device clusters |
| `complaints.csv` | [backend/data/complaints.csv](backend/data/complaints.csv) | Synthetic NCRP victim complaint records with loss amounts and incident descriptions |
| `expected_results.json` | [backend/data/expected_results.json](backend/data/expected_results.json) | Ground-truth expected fraud rings (`S01` to `S09`) for automated evaluation |
| `formatted_synthetic_alerts.json` | [backend/data/formatted_synthetic_alerts.json](backend/data/formatted_synthetic_alerts.json) | 24 precomputed evidence-linked alerts matching backend detection schemas |

---

## 6. Technology Stack

### Frontend Architecture
- **Framework**: [React 18](https://react.dev/) / [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite 5](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Graph Visualization**: [Cytoscape.js](https://js.cytoscape.org/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Testing**: Node test runner (`tests/*.test.mjs`)
- **Hosting**: [Vercel](https://anvik-frontend-alpha.vercel.app)

### Backend Architecture
- **Language & Runtime**: [Python 3.11+](https://www.python.org/)
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Graph Modeling**: [NetworkX 3.x](https://networkx.org/)
- **Cloud Database**: [Turso hosted libSQL](https://turso.tech/) (via `turso_serverless`)
- **Testing Suite**: [pytest](https://docs.pytest.org/), HTTPX
- **Hosting**: [Vercel Serverless Python](https://anvik-backend.vercel.app)

---

## 7. Local Development & Quickstart

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/bharath-0814/anvik.git
cd anvik
```

### 2. Backend Setup
```bash
# Create and activate Python virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run backend test suite (88 passing unit & integration tests)
pytest backend/tests

# Launch local FastAPI development server
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Local API docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Run frontend test suite (13 passing tests)
npm test

# Build for production
npm run build

# Launch local Vite development server
npm run dev
```
Local frontend will be running at [http://localhost:5173](http://localhost:5173).

---

## 8. Team Ownership & Responsibilities

The Anvik project is organized across strict team member ownership boundaries:

### Piyush — Members 1 & 2: Frontend Development, UI/UX & Graph Visualization
- Owns the entire frontend codebase, UI design, component layout, and user experience.
- Interactive Cytoscape.js canvas for visualizing multi-hop accounts, devices, and money flows.
- Node/edge styling, layout physics, zoom/pan controls, timeline scrubbing, and case management.
- Integration with backend REST APIs via typed services.

### Bharath — Member 3: Backend, Database & Fraud Detection Engine
- **Sole owner of the entire backend, database, and detection engine.**
- FastAPI application architecture, Pydantic schemas, and REST endpoint design.
- Turso hosted libSQL database integration, migrations, and repository access layers.
- NetworkX directed multigraph modeling, traversal algorithms, and cycle detection.
- Deterministic fraud detection rules, mathematical priority scoring, and counterfactual analysis.
- Automated testing suite (88 pytest tests) and serverless Vercel deployment.

### Aryan — Member 4: Synthetic Dataset Validation, Quality & QA
- Synthetic dataset schema validation, data quality checks, and referential integrity audits.
- Authoring benchmark ground-truth outcomes and edge-case evaluation scenarios.
- Verifying detection engine precision, false-positive resistance, and boundary conditions.

### Shivam — Member 5: Synthetic Transaction Dataset Engineering
- Synthesizing realistic financial entities: accounts, devices, merchants, transactions, and complaints.
- Embedding complex fraud ring topologies (layering chains, multi-source fan-in, circular loops, shared devices).
- Ensuring data realism across timestamps, amount distributions, and Indian banking entities.

### Member 6 (Unconfirmed): Demo, Presentation & PPT
- Demonstration scenarios, walkthrough narratives, and investigator storytelling scripts.
- Presentation slide deck, architecture diagrams, and submission deliverables.
- Hackathon rehearsal coordination and live presentation delivery.

---

## 9. Technical Documentation & Specifications

Internal technical specifications and architecture records are maintained within the repository:

- **[LICENSE](LICENSE)**: Open-source MIT License terms and copyright.
- **[SECURITY.md](SECURITY.md)**: Security policy, synthetic data exclusivity, and responsible disclosure.
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines, commit conventions, and ownership rules.
- **[.github/workflows/ci.yml](.github/workflows/ci.yml)**: Continuous Integration pipeline running pytest (88 tests) and Vite build (13 tests).
- **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)**: Formal REST API contract, request/response models, and error states.
- **[docs/DECISIONS.md](docs/DECISIONS.md)**: Architectural Decision Records (ADRs) detailing database selection, scoring models, and Vercel hosting.
- **[docs/FLOW.md](docs/FLOW.md)**: End-to-end Mermaid sequence and data-flow diagrams mapping intake to detection.
- **[AGENTS.md](AGENTS.md)**: Contributor governance, member boundaries, and coding standards.
- **[GEMINI.md](GEMINI.md)**: AI agent instructions and operational guidelines.
- **[frontend/README.md](frontend/README.md)**: Detailed frontend architecture, component layout, and build guide.

---

## 10. Compliance & Ethical Disclaimers

1. **Synthetic Data Exclusivity**: All names, virtual payment addresses (VPAs), account numbers, device identifiers, amounts, and transaction records in this project are 100% synthetically generated for academic and hackathon evaluation purposes. Any resemblance to real individuals or active accounts is purely coincidental.
2. **Decision Support Nature**: Anvik is designed as an investigative workbench that highlights patterns warranting closer inspection by qualified forensic analysts. Automated risk scores and rule alerts must never be treated as legal determinations of guilt or liability.
3. **Zero Credentials**: The codebase contains zero committed credentials, live API keys, or proprietary secrets. All production database connections use secure environment variables.
