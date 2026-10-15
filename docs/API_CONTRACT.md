# Anvik API Contract & Schema Reconciliation Specification

> **PS 16 — UPI Fraud-Ring Graph Investigator with Explainable Alerts**  
> *Phase 5B — Multi-Member Contract Alignment (Aryan, Piyush, Bharath)*

---

## 1. Overview & Architectural Role

This document specifies the authoritative HTTP API contracts, data models, and schema reconciliations between:
1. **Aryan (Member 4)**: Fraud-detection engine rules, alert bundle JSON contract (`anvik_expected_results_v1.json`), and scoring formula.
2. **Piyush (Members 1 & 2)**: Frontend UI/UX, Cytoscape.js network explorer (`bharath-0814/anvik-frontend`), and investigation dossiers.
3. **Bharath (Member 3)**: Backend architecture, Turso hosted SQL database, NetworkX graph engine, and FastAPI endpoints.

> [!IMPORTANT]
> **Investigative Decision Support Only**: Anvik alerts and risk scores represent deterministic analytical leads for human investigators, not automated declarations of guilt or legal proof.
> 
> **Synthetic Data Only**: All account identifiers, VPAs, transaction IDs, device tokens, and complaints are synthetic.

---

## 2. Currently Implemented & Live Backend Endpoints

### 2.1 Service Health (Liveness Probe)
- **Path**: `GET /api/health`
- **Purpose**: Fast, independent liveness check. Returns HTTP 200 OK regardless of database or network state.
- **Response Model**:
  ```json
  {
    "status": "healthy",
    "service": "anvik-backend"
  }
  ```

### 2.2 Database Readiness Probe
- **Path**: `GET /api/ready`
- **Purpose**: Verifies that the Turso database (`libsql://...`) is reachable and executing queries.
- **Response Model (Success: HTTP 200 OK)**:
  ```json
  {
    "status": "ready",
    "database": {
      "connected": true,
      "message": "Database connection successful"
    },
    "environment": "development"
  }
  ```
- **Response Model (Failure: HTTP 503 Service Unavailable)**:
  ```json
  {
    "detail": "Database unavailable: <safe_error_message>"
  }
  ```

### 2.3 Cytoscape Transaction & Device Interaction Graph
- **Path**: `GET /api/graph`
- **Query Parameters**:
  - `status` (*optional*, `string`): Filter transactions by execution status (e.g. `SUCCESS`, `FAILED`).
  - `limit` (*optional*, `integer`, `ge=1`): Restrict transaction count for bounded graph exploration.
- **Response Model**: `GraphResponse` (Cytoscape.js standard JSON)
  ```json
  {
    "nodes": [
      {
        "data": {
          "id": "acc:ACC0001",
          "label": "ACC0001",
          "node_type": "account",
          "account_id": "ACC0001",
          "holder_name": "Aarav Nair",
          "vpa": "aarav.nair1@synaxis",
          "bank": "AXIS",
          "device_id": null
        }
      },
      {
        "data": {
          "id": "dev:DEV0163",
          "label": "DEV0163",
          "node_type": "device",
          "account_id": null,
          "holder_name": null,
          "vpa": null,
          "bank": null,
          "device_id": "DEV0163"
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "link:ACC0001_DEV0163",
          "source": "acc:ACC0001",
          "target": "dev:DEV0163",
          "edge_type": "uses_device",
          "txn_id": null,
          "amount_paise": null,
          "amount_inr": null,
          "timestamp_utc": null,
          "raw_timestamp": null,
          "txn_type": null,
          "status": null,
          "device_id": "DEV0163"
        }
      },
      {
        "data": {
          "id": "txn:TXN000102",
          "source": "acc:ACC0001",
          "target": "acc:ACC0157",
          "edge_type": "transaction",
          "txn_id": "TXN000102",
          "amount_paise": 30886,
          "amount_inr": 308.86,
          "timestamp_utc": "2026-09-03T18:19:51+00:00",
          "raw_timestamp": "2026-09-03 23:49:51",
          "txn_type": "PAY",
          "status": "SUCCESS",
          "device_id": "DEV0163"
        }
      }
    ],
    "metadata": {
      "dataset_id": "shivam_sample_1",
      "node_count": 396,
      "edge_count": 3362,
      "account_node_count": 200,
      "device_node_count": 196,
      "transaction_edge_count": 3129,
      "device_edge_count": 233,
      "generated_at_utc": "2026-10-16T05:37:22Z"
    }
  }
  ```

---

## 3. Proposed Common Alert & Bundle Contract (`GET /api/alerts`)

Aryan is currently finalizing the detection engine rule thresholds and multi-factor scoring formula. To prevent breaking changes, the following schema reconciles Aryan's bundle-level structure with Piyush's frontend UI expectations.

### 3.1 Alert Record Schema (`AlertRecord`)

```typescript
interface AlertRecord {
  // Primary Identifiers
  alert_id: string;               // Unique ID: e.g. "ALT-2026-ROT-001"
  rule_id: string;                // Rule ID: "RAPID_ONWARD_TRANSFER" | "TRANSACTION_CYCLE" | "MULTIPLE_SOURCE_FAN_IN"
  title: string;                  // Human-readable title: "Rapid Onward Fund Dispersal Detected"
  
  // Prioritization & Scoring (Maintained adaptable pending Aryan's final formula)
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";
  score: number;                  // Normalized heuristic ranking (0.0 to 100.0)
  
  // Temporal Metadata
  created_at: string;             // ISO-8601 UTC timestamp: "2026-09-03T18:30:00Z"
  
  // Associated Entity Identifiers
  account_ids: string[];          // Primary involved account IDs: ["ACC0001", "ACC0002"]
  vpas: string[];                 // Associated VPAs: ["aarav.nair1@synaxis"]
  txn_ids: string[];              // Direct trigger transactions: ["TXN000102", "TXN000103"]
  linked_txn_ids?: string[];      // Multi-hop contextual transactions: ["TXN000104"]
  complaint_ids?: string[];       // Linked NCRP complaints: ["CMP0001"]
  related_alert_ids?: string[];   // Co-occurring alerts in the same subgraph
  ring_id?: string | null;        // Cluster ID if mapped to a multi-entity syndicate: "RING-01"
  
  // Explainability & Transparent Decision Support
  explanation: string;            // Plain-English narrative describing the exact observed flow
  limitations: string[];          // Known data limits: ["No merchant categorization available", "Single-device observation"]
  alternative_explanations: string[]; // Legitimate business hypotheses: ["Festival group expense collection", "Vendor batch settlement"]
  would_clear_if?: string[];      // Counterfactual conditions: ["Outward transaction is verified as vendor invoice payment"]
  informational_only: boolean;    // If true, presented as context rather than a high-confidence alert
  
  // Quantitative Evidence Metrics
  evidence: {
    matched_records: {
      inflow_amount_inr?: number;
      outflow_amount_inr?: number;
      forwarding_ratio?: number;
      time_delta_seconds?: number;
      cycle_length?: number;
      incoming_source_count?: number;
      disputed_amount_inr?: number;
    };
    counterfactual_summary?: {
      immediate_freeze_impact_inr?: number;
      severed_downstream_hops?: number;
    };
    network_context?: {
      shared_device_detected?: boolean;
      device_id?: string;
    };
  };

  // Subgraph Context (Optional on list, included on detail)
  graph?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    is_truncated: boolean;
    disclaimer: string;
  };
}
```

### 3.2 Full Alert Bundle Schema (`AlertBundle`)

For batch exports, scenario evaluations, and benchmark grading:

```typescript
interface AlertBundle {
  dataset_id: string;             // Identifier of synthetic dataset: "anvik_v1"
  generated_at: string;           // ISO-8601 UTC: "2026-10-16T00:00:00Z"
  amount_unit: "INR";             // Explicit currency unit
  count: number;                  // Total alerts in bundle (must match alerts.length)
  meta: {
    engine_version: string;       // "0.1.0"
    total_transactions_scanned: number;
    total_accounts_scanned: number;
    execution_time_ms: number;
  };
  alerts: AlertRecord[];
  rings: RingRecord[];
  account_summaries: AccountSummary[];
}

interface RingRecord {
  ring_id: string;                // "RING-01"
  pattern_type: "MULE_RING" | "DEVICE_FARM" | "CIRCULAR_ROUTING" | "FAN_IN_DISPERSAL";
  alert_ids: string[];
  account_ids: string[];
  total_volume_inr?: number;
}

interface AccountSummary {
  account_id: string;
  vpa?: string;
  role?: "origin_victim" | "aggregator_mule" | "secondary_mule" | "cashout_endpoint" | "normal_counterparty";
  total_sent_inr?: number;
  total_received_inr?: number;
  flagged_alert_count?: number;
}
```

---

## 4. Reconciled Differences & Architectural Conventions

| Discrepancy Point | Backend Standard (`anvik`) | Frontend Model (`avnikfrontend`) | Reconciled Contract & Adapter Strategy |
|---|---|---|---|
| **Risk Score Representation** | `score: float` (0.0 to 100.0 heuristic ranking) | `riskScore: number` (0 to 100) or `confidenceScore` | **Heuristic Ranking Only**. The score is strictly an investigative priority rank (0–100), **never a probability of guilt**. Aryan's final formula will define weights. Frontend maps `score` directly to `riskScore`. |
| **Priority / Severity Labels** | `priority: "CRITICAL" \| "HIGH" \| "MEDIUM" \| "LOW" \| "INFORMATIONAL"` | `severity: "CRITICAL" \| "HIGH" \| "MEDIUM" \| "LOW"` | **Uppercase Enum**. Both systems use uppercase string literals. Backend adds `INFORMATIONAL` for baseline controls. |
| **Currency Fields** | `amount_inr: float` and `amount_paise: int` | `amount: number` | Backend provides `amount_inr` (rupees) and `amount_paise` (integer precision). Frontend adapter maps `amount_inr` to `amount`. |
| **Edge Type vs Channel** | `edge_type: "transaction" \| "uses_device"` | `channel: "UPI_P2P" \| "DEVICE_BIND"` | Frontend adapter maps: `uses_device` ➔ `"DEVICE_BIND"`, `transaction` ➔ `"UPI_P2P"`. |
| **Node ID Prefixing** | Prefixed: `acc:ACC0001`, `dev:DEV0001` | Raw or custom IDs: `ACC_VICTIM_1`, `DEV_MULE_1` | **Backend Prefixes Preserved**. Cytoscape node IDs must use `acc:` and `dev:` prefixes to prevent ID collisions across accounts and hardware devices. |
| **Graph Subgraph Payload** | Bounded full graph returned via `GET /api/graph` | Nested `graph: { nodes, edges }` on alert detail | **Decoupled Architecture**. `GET /api/graph` provides global/filtered topology. When `GET /api/alerts/{id}` is queried, it returns an alert-bounded 2-hop neighborhood. |
| **Ring Membership** | Explicit `rings: RingRecord[]` and `ring_id` on alert | `clusterId: string` | `ring_id` on the alert maps directly to frontend `clusterId`. Ring metadata provides aggregated volume and participant lists. |

---

## 5. Scope Boundaries

1. **No Competing Detection Engine**: Bharath will not generate alternative scoring formulas or preempt Aryan's engine deliverables.
2. **Read-Only MVP Pipeline**: In accordance with hackathon time constraints, user-facing complaint creation forms are descoped. All complaint views consume preloaded synthetic records.
3. **Transparent Heuristics**: If `GET /api/alerts` is queried prior to Aryan's engine release, it returns only alerts produced by verified, registered detection rules (`RAPID_ONWARD_TRANSFER`, `TRANSACTION_CYCLE`, `MULTIPLE_SOURCE_FAN_IN`), never synthetic mock alerts disguised as live detections.
