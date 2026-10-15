# Anvik

> **PS 16 — UPI Fraud-Ring Graph Investigator**  
> *Code-e-Manipal Hackathon Project*

---

## 1. Project Identity and Objective

**Anvik** is an investigative decision-support system designed to detect and explore coordinated UPI fraud patterns across interconnected synthetic transaction entities (accounts, devices, merchants, and complaints).

Anvik constructs a graph of synthetic financial interactions to surface explainable, evidence-backed transaction clusters, timeline anomalies, and counterfactual insights for fraud analysts and investigators.

> [!IMPORTANT]
> **Investigative Decision Support Only**: Anvik is an analytical aid for investigators, not an automated system for declaring individuals guilty. Suspicious alerts, graph anomalies, and shared identifiers represent investigative leads, not legal proof of wrongdoing.

> [!NOTE]
> **Synthetic Data Policy**: Anvik exclusively operates on synthetic transaction datasets. It does not connect to real banking infrastructure, payment gateways, live customer financial records, or real personal credentials.

---

## 2. Planned Features

- **Interactive Transaction Graphs**: Dynamic exploration of accounts, devices, merchants, and transactions using Cytoscape.js.
- **Evidence-Linked Alerts**: Transparent priority scoring that explains why a pattern was flagged with exact supporting evidence.
- **Transaction Timelines**: Visual chronological progression of transactions, identifying rapid dispersion or cycling.
- **Complaint Associations**: Linking formal complaints and dispute reports to transaction entities and clusters.
- **Explainable Detection Rules**: Deterministic rules identifying structuring, shared device misuse, mule routing, and circular funds.
- **Counterfactual Analysis**: Investigating hypothetical scenarios (e.g., removing a bridge node or modifying a link) to evaluate cluster fragility.
- **Case Management**: Workflow tools to track ongoing investigations, bookmark entities, and record analyst findings.

---

## 3. Technology Stack

### Frontend (Owned by Piyush — Members 1 & 2)
- **Framework & Language**: React 18 / TypeScript
- **Tooling & Build**: Vite
- **Styling & UI**: Tailwind CSS, shadcn/ui, Lucide React
- **Routing**: React Router
- **Graph Visualization**: Cytoscape.js
- **Testing**: Vitest, React Testing Library

### Backend (Owned by Bharath — Member 3)
- **Language & Runtime**: Python 3.11+
- **API Framework**: FastAPI, Uvicorn, Pydantic
- **Database & Storage**: Turso hosted SQL (via `turso_serverless`)
- **Graph Engine & Processing**: NetworkX, Pandas, NumPy
- **Testing & Verification**: pytest, HTTPX

---

## 4. Current Development Status

**Status: Backend Foundation Phase.**

- **Backend Foundation**: Active implementation of FastAPI application structure, Pydantic schemas, Turso database connection, NetworkX graph engine, and rule-based detection logic.
- **Data Engineering Handoff**: The finalized synthetic JSON dataset (`anvik_dataset_v1.json`) and ground-truth expected detection results (`anvik_expected_results_v1.json`) are currently being generated and validated by Shivam (Dataset Generation) and Aryan (QA & Validation).
- **Frontend Preparation**: UI component scaffolding and Cytoscape.js graph canvas preparation will integrate with backend endpoints once the foundation is active.
- **Data Policy & Ethics**: Strict synthetic data only policy is enforced across all environments. All flagged patterns serve as investigative leads, not proof of guilt.

---

## 5. Team Ownership & Responsibilities

The Anvik project is organized across defined member ownership boundaries:

### Piyush — Members 1 & 2: Frontend Development, UI/UX & Graph Visualization
- Owns the entire frontend codebase, UI/UX design, and presentation layer.
- React 18, TypeScript, Vite, Tailwind CSS, and shadcn/ui component architecture.
- Interactive Cytoscape.js graph canvas for visualizing accounts, devices, merchants, transactions, and complaints.
- Node/edge styling, layouts, zoom/pan controls, path highlighting, and graph filtering.
- Transaction timelines, complaint forms, evidence inspector, and case management UI.
- Direct integration with Bharath's backend REST APIs.

### Bharath — Member 3: Backend, Database & Fraud Detection Engine
- **Sole owner of the entire backend, database, and detection engine.**
- Python 3.11+ FastAPI service architecture and Pydantic request/response validation.
- Turso hosted SQL database schema, queries, and client connectivity (via `turso_serverless`).
- Synthetic dataset ingestion and validation service (`anvik_dataset_v1.json`).
- NetworkX graph construction, cycle detection, path traversal, and community analysis.
- Rule-based fraud detection engine (structuring, mule fan-out/fan-in, circular routing, high-risk device sharing).
- Evidence-linked alert generation and explainable priority scoring.
- Counterfactual analysis engine (node/edge perturbation and impact assessment).
- Automated backend testing suite (pytest, HTTPX) and deployment configuration.

### Aryan — Member 4: Synthetic Dataset Validation, Quality & QA
- Synthetic dataset validation, data quality checks, and schema conformance.
- Authoring test scenarios, edge cases, and ground-truth expected outcomes (`anvik_expected_results_v1.json`).
- Verifying detection engine accuracy, false positive rates, and rule precision.
- Handoff validation between synthetic data generation and backend ingestion.

### Shivam — Member 5: Synthetic Transaction Dataset Engineering
- Generates comprehensive synthetic transaction datasets (`anvik_dataset_v1.json`).
- Synthesizes realistic entities: accounts, devices, merchants, transactions, and complaints.
- Plants distinct fraud ring topologies alongside realistic benign control transactions.
- Coordinates data structure alignment with Aryan (QA) and Bharath (Backend).

### Member 6 (Unconfirmed): Demo, Presentation & PPT
- Demonstrations, walkthrough scenarios, and investigator storytelling scripts.
- Presentation slide deck, architecture diagrams, and submission deliverables.
- Rehearsal coordination and live presentation delivery.

---

## 6. Proposed Development Sequence

1. **Phase 1: Repository Initialization & Ownership** — Project hygiene, configuration, team boundaries, and documentation scaffold.
2. **Phase 2: Synthetic Data & Ground Truth Generation** — Creation of `anvik_dataset_v1.json` (Shivam) and validation of `anvik_expected_results_v1.json` (Aryan).
3. **Phase 3: Backend Foundation & Detection Engine (Current)** — FastAPI endpoints, Turso database integration, NetworkX graph modeling, detection rules, and counterfactual engine (Bharath).
4. **Phase 4: Frontend Development & Graph Visualization** — UI dashboard, Cytoscape.js canvas, and evidence panels (Piyush).
5. **Phase 5: API Integration & Case Management** — End-to-end integration between frontend and backend APIs.
6. **Phase 6: Verification, Rehearsal & Demonstration** — Ground-truth benchmark verification, demonstration walk-throughs, slide deck finalization, and deployment.
