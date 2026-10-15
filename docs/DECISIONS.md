# Architecture and Implementation Decision Log (DECISIONS.md)

This document records meaningful architectural, implementation, data-model, security, testing, and integration decisions made throughout the development of the **Anvik** backend and detection engine.

Format per entry:
- **Date/Time (UTC)**
- **Decision**
- **Status** (accepted, changed, superseded, proposed)
- **Context / Problem**
- **Reason & Rationale**
- **Alternatives Considered**
- **Consequences & Trade-offs**
- **Affected Files / Components**
- **Verification Method / Test Result**

---

### DEC-001: Adoption of Turso (libSQL) as Primary Database
- **Date/Time (UTC):** 2026-10-15 14:00:00Z
- **Decision:** Use Turso (hosted libSQL / SQLite compatible) via `turso_serverless` driver for persistent storage, and standard `sqlite3` for local hermetic testing.
- **Status:** accepted (verified)
- **Context / Problem:** Anvik requires a lightweight, zero-maintenance relational database suitable for hackathon deployment, fast schema iteration, and serverless hosting on Render.
- **Reason & Rationale:** Turso provides SQLite compatibility over HTTP/WebSocket, eliminates heavyweight PostgreSQL server overhead, allows in-memory local unit tests using Python's standard `sqlite3` module, and deploys effortlessly on free-tier infrastructure.
- **Alternatives Considered:** PostgreSQL with SQLAlchemy & Alembic (rejected due to configuration overhead, connection pooling complexity, and hosting costs).
- **Consequences & Trade-offs:** Foreign key enforcement must be handled at the application/importer layer; migrations must avoid vendor-specific PostgreSQL extensions and stick to standard SQLite syntax.
- **Affected Files / Components:** `backend/app/db/turso.py`, `backend/app/core/config.py`, `backend/app/db/migrations.py`.
- **Verification Method / Test Result:** Remote `SELECT 1` verified against `libsql://anvik-bharath-0814.aws-ap-south-1.turso.io`; unit tests in `backend/tests/test_turso_connection.py` passing (6/6).

---

### DEC-002: Backend API Framework Selection (FastAPI)
- **Date/Time (UTC):** 2026-10-15 15:00:00Z
- **Decision:** Use FastAPI with Uvicorn and Pydantic v2 as the backend REST API framework.
- **Status:** accepted (verified)
- **Context / Problem:** Need high-performance, asynchronous-capable REST endpoints with automatic OpenAPI schema generation for frontend integration (Piyush).
- **Reason & Rationale:** FastAPI offers native Pydantic validation, explicit type safety, self-documenting interactive docs (`/docs`), and clean dependency injection.
- **Alternatives Considered:** Flask (rejected: lack of native Pydantic validation and async support), Django (rejected: overly heavy for a microservice architecture).
- **Consequences & Trade-offs:** Requires strict Pydantic model hygiene; synchronous DB-API calls must be run cleanly without blocking async event loops.
- **Affected Files / Components:** `backend/app/main.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/ready.py`, `backend/app/api/routes/graph.py`.
- **Verification Method / Test Result:** Health and readiness endpoints verified via `fastapi.testclient.TestClient` (`backend/tests/test_health.py`, `backend/tests/test_ready.py`).

---

### DEC-003: Timestamp and Currency Normalization Standard
- **Date/Time (UTC):** 2026-10-15 17:30:00Z
- **Decision:** Raw dataset timestamps are parsed as Indian Standard Time (`Asia/Kolkata`, IST, UTC+05:30) when naive, and stored as standardized UTC ISO 8601 strings with timezone offset (`+00:00`). Transaction amounts are validated as INR with at most 2 decimal places, converted to integer paise (`amount_paise`) for exact arithmetic, and stored as float INR (`amount_inr`) for fast querying.
- **Status:** accepted (verified)
- **Context / Problem:** Source transaction data from Shivam contained naive timestamps recorded in IST and decimal amounts that could suffer from floating-point rounding errors.
- **Reason & Rationale:** Consistent UTC timestamps ensure proper chronological comparisons across time zones; paise representation prevents floating-point imprecision in financial balance calculations.
- **Alternatives Considered:** Storing naive timestamps (rejected: causes ordering bugs when daylight savings or multi-region queries occur); floating point currency only (rejected: precision loss).
- **Consequences & Trade-offs:** Ingestion requires explicit parsing and conversion functions.
- **Affected Files / Components:** `backend/app/services/validator.py`, `backend/app/services/importer.py`, `backend/migrations/001_initial_schema.sql`.
- **Verification Method / Test Result:** Verified in `backend/tests/test_validation.py` (14/14 tests passing).

---

### DEC-004: NetworkX MultiDiGraph for In-Memory Graph Representation
- **Date/Time (UTC):** 2026-10-15 19:30:00Z
- **Decision:** Use `networkx.MultiDiGraph` to model transaction networks in memory, serializing to Cytoscape.js JSON format for frontend rendering.
- **Status:** accepted (verified)
- **Context / Problem:** Transactions between accounts are directional and accounts can exchange multiple transactions over time; simple graphs (`DiGraph`) collapse multiple edges into one.
- **Reason & Rationale:** `MultiDiGraph` preserves every individual transaction edge, its timestamp, amount, and status while providing standard graph algorithms (subgraph extraction, path finding, degree calculation).
- **Alternatives Considered:** Graph databases like Neo4j (rejected: deployment and resource overhead for hackathon scale); simple directed graph (rejected: collapses multiple transactions between same pair).
- **Consequences & Trade-offs:** Graph queries load relevant subgraphs from relational DB into memory; bounded with query limits (`limit` parameter) to maintain low latency.
- **Affected Files / Components:** `backend/app/services/graph.py`, `backend/app/api/routes/graph.py`, `backend/app/schemas/graph.py`.
- **Verification Method / Test Result:** Subgraph generation, filtering, and Cytoscape.js export verified in `backend/tests/test_graph.py` (6/6 tests passing).

---

### DEC-005: Idempotent Dataset Importer with SHA-256 Hashing
- **Date/Time (UTC):** 2026-10-15 20:30:00Z
- **Decision:** Implement content-addressable SHA-256 hashing over incoming CSV files to ensure idempotent, repeatable imports into Turso/SQLite.
- **Status:** accepted (verified)
- **Context / Problem:** Re-running import scripts or server restarts must not duplicate database records or create orphan rows.
- **Reason & Rationale:** A dedicated `dataset_imports` table tracks applied dataset hashes. If identical data is submitted without `force=True`, the import returns a safe no-op.
- **Alternatives Considered:** Blind truncation and reload (rejected: risks downtime during re-ingestion); simple row count comparison (rejected: does not detect internal content edits).
- **Consequences & Trade-offs:** Requires reading and hashing input data prior to executing insert transactions.
- **Affected Files / Components:** `backend/app/services/importer.py`, `backend/app/db/repository.py`, `backend/migrations/001_initial_schema.sql`.
- **Verification Method / Test Result:** Idempotency and replace behavior verified in `backend/tests/test_importer.py` (5/5 tests passing).

---

### DEC-006: Explainable, Evidence-Linked Alert Architecture
- **Date/Time (UTC):** 2026-10-15 22:00:00Z
- **Decision:** All fraud detection alerts must contain structured, quantitative evidence (`HopEvidence`, flow metrics, ratios), transparent natural language narratives, explicit limitations, and plausible alternative non-fraud explanations.
- **Status:** accepted (verified)
- **Context / Problem:** Black-box fraud scores fail regulatory scrutiny and provide zero investigative decision support. Antigravity rules (Rule 13 and Rule 14) require alerts to be decision-support aids, not accusations of guilt.
- **Reason & Rationale:** Investigators must know *why* a pattern was flagged, what parameters triggered it, and what legitimate commercial or personal activities could account for the pattern.
- **Alternatives Considered:** Raw probabilistic risk score (rejected: uninterpretable, high false-accusation risk).
- **Consequences & Trade-offs:** Alert payloads carry more metadata; rules must formulate detailed evidence objects alongside detection matches.
- **Affected Files / Components:** `backend/app/detection/models.py`, `backend/app/detection/base.py`, `backend/app/detection/rules/`.
- **Verification Method / Test Result:** Verified across all rule unit tests in `backend/tests/test_detection_rapid_transfer.py` and `backend/tests/test_detection_cycle.py`.

---

### DEC-007: Modular Scoring Architecture Pending Finalized Formula
- **Date/Time (UTC):** 2026-10-15 22:30:00Z
- **Decision:** Decouple pattern detection logic from scoring. Implement a replaceable heuristic baseline in `backend/app/detection/scoring.py` while Aryan (Member 4) develops the finalized multi-factor scoring formula.
- **Status:** accepted (verified)
- **Context / Problem:** Detection rules need priority scoring for alert sorting and UI presentation, but the formal statistical scoring formula is an ongoing work stream by Member 4.
- **Reason & Rationale:** Isolating `calculate_alert_score()` ensures that rules never embed hardcoded or arbitrary scoring math, allowing drop-in replacement when Aryan hands off the finalized scoring model.
- **Alternatives Considered:** Embedding scoring directly inside each detection rule class (rejected: creates massive refactor debt when formula changes).
- **Consequences & Trade-offs:** Initial scores represent heuristic prioritization indicators rather than calibrated statistical probabilities.
- **Affected Files / Components:** `backend/app/detection/scoring.py`, `backend/app/detection/rules/rapid_transfer.py`, `backend/app/detection/rules/transaction_cycle.py`.
- **Verification Method / Test Result:** Unit tests verify score bounds in $[0.0, 100.0]$ and override capabilities.

---

### DEC-008: Simplification of Hackathon Scope (No User Complaint Intake Form)
- **Date/Time (UTC):** 2026-10-15 23:45:00Z
- **Decision:** Descope interactive user-facing complaint submission forms, live user registration, and intake endpoints for the hackathon MVP. Focus exclusively on investigative search over preloaded synthetic datasets and preloaded complaint records.
- **Status:** accepted (verified)
- **Context / Problem:** Time constraints for the hackathon require focusing engineering bandwidth on core investigative value: transaction search, graph exploration, evidence inspection, and detection rules.
- **Reason & Rationale:** Existing preloaded complaint records from Shivam's dataset already provide ground truth for victim-linked rings and convergence rules. Building user intake forms adds UI and validation overhead without advancing graph investigation capabilities.
- **Alternatives Considered:** Building full CRUD complaint management endpoints (rejected: distracts from graph engine and detection rules).
- **Consequences & Trade-offs:** Complaints are preloaded via synthetic dataset ingestion rather than dynamic user submission.
- **Affected Files / Components:** Backend API routing, `docs/WORK_PLAN.md`, architectural roadmap.
- **Verification Method / Test Result:** Verified absence of unnecessary intake routes; complaint convergence tested via database lookup helper `get_complaints_lookup()`.

---

### DEC-009: Rule 2 Implementation — Directed Transaction Cycle Detection
- **Date/Time (UTC):** 2026-10-16 04:25:00Z
- **Decision:** Implement `TransactionCycleRule` using bounded depth-first search (DFS) over chronologically ordered `SUCCESS` transactions, enforcing configurable cycle duration (default 4.0h), amount retention ratios ($0.70$ to $1.25$), and canonical transaction set deduplication.
- **Status:** accepted (verified)
- **Context / Problem:** Fraud rings cycle funds across circular accounts ($A \to B \to C \to A$) to artificially inflate volume or obfuscate fund origin. Legitimate settlements (e.g. roommates settling bills over several days with varied amounts) must NOT be flagged.
- **Reason & Rationale:**
  - Rapid loops (e.g., $S05\_CYCLE$, 41 minutes, 98% retained) exhibit high velocity and tight amount retention.
  - Normal roommate settle-ups ($S06\_ROOMMATE\_SETTLEUP$, 94.7 hours, disparate amounts) naturally fall outside the 4.0-hour window and retention bounds.
  - Canonical transaction key deduplication (`tuple(sorted(txn_ids))`) prevents the same circular loop from emitting multiple alerts when traversed from different nodes.
- **Alternatives Considered:** Simple cycle detection in static graph via `nx.simple_cycles` (rejected: ignores transaction timestamps, chronological causality, and hop amounts).
- **Consequences & Trade-offs:** DFS exploration is bounded by `max_cycle_length` (default 5 hops) to ensure linear/polynomial time complexity over high-volume transaction sets.
- **Affected Files / Components:** `backend/app/detection/rules/transaction_cycle.py`, `backend/app/detection/rules/__init__.py`, `backend/app/detection/registry.py`, `backend/app/detection/scoring.py`, `backend/tests/test_detection_cycle.py`.
- **Verification Method / Test Result:** Verified with ground truth: $S05\_CYCLE$ detected with exact accounts `['ACC0101', 'ACC0102', 'ACC0103']` and transactions `['TXN002702', 'TXN002703', 'TXN002705']`; $S06\_ROOMMATE\_SETTLEUP$ is completely unflagged. 10/10 tests passing in `backend/tests/test_detection_cycle.py`.
