"""Unit tests for NetworkX graph engine and Cytoscape.js API route."""

import sqlite3
from typing import Generator
from unittest.mock import patch

import networkx as nx
import pytest
from app.api.routes.graph import get_db
from app.db.migrations import run_migrations
from app.main import app
from app.services.graph_service import (
    build_networkx_graph,
    get_graph_data,
)
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def populated_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide an in-memory SQLite database populated with standard test data."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    run_migrations(conn)

    cursor = conn.cursor()
    # Accounts
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, "
        "raw_created_at, created_at_utc) "
        "VALUES ('ACC0001', 'Alice', 'alice@okhdfcbank', 'HDFC', "
        "'2026-09-01 10:00:00', '2026-09-01T04:30:00+00:00');"
    )
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, "
        "raw_created_at, created_at_utc) "
        "VALUES ('ACC0002', 'Bob', 'bob@oksbi', 'SBI', "
        "'2026-09-01 11:00:00', '2026-09-01T05:30:00+00:00');"
    )
    cursor.execute(
        "INSERT INTO accounts (account_id, holder_name, vpa, bank, "
        "raw_created_at, created_at_utc) "
        "VALUES ('ACC0003', 'Charlie', 'charlie@okaxis', 'AXIS', "
        "'2026-09-01 12:00:00', '2026-09-01T06:30:00+00:00');"
    )

    # Devices
    cursor.execute("INSERT INTO devices (device_id) VALUES ('DEV0001');")
    cursor.execute("INSERT INTO devices (device_id) VALUES ('DEV0002');")

    # Account-Device Links
    cursor.execute(
        "INSERT INTO account_devices (account_id, device_id) VALUES ('ACC0001', 'DEV0001');"
    )
    cursor.execute(
        "INSERT INTO account_devices (account_id, device_id) VALUES ('ACC0002', 'DEV0001');"
    )  # shared device!
    cursor.execute(
        "INSERT INTO account_devices (account_id, device_id) VALUES ('ACC0003', 'DEV0002');"
    )

    # Transactions (including parallel edges between ACC1 and ACC2)
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, "
        "timestamp_utc, txn_type, status, device_id) VALUES "
        "('TXN001', 'ACC0001', 'ACC0002', 'alice@okhdfcbank', 'bob@oksbi', 50000, "
        "500.0, '2026-09-02 10:00:00', '2026-09-02T04:30:00+00:00', 'PAY', 'SUCCESS', 'DEV0001');"
    )
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, "
        "timestamp_utc, txn_type, status, device_id) VALUES "
        "('TXN002', 'ACC0001', 'ACC0002', 'alice@okhdfcbank', 'bob@oksbi', 25000, "
        "250.0, '2026-09-02 10:05:00', '2026-09-02T04:35:00+00:00', 'PAY', 'SUCCESS', 'DEV0001');"
    )
    cursor.execute(
        "INSERT INTO transactions (txn_id, sender_account_id, receiver_account_id, "
        "sender_vpa, receiver_vpa, amount_paise, amount_inr, raw_timestamp, "
        "timestamp_utc, txn_type, status, device_id) VALUES "
        "('TXN003', 'ACC0002', 'ACC0003', 'bob@oksbi', 'charlie@okaxis', 70000, "
        "700.0, '2026-09-02 11:00:00', '2026-09-02T05:30:00+00:00', 'PAY', 'FAILED', 'DEV0001');"
    )

    # Dataset Import record
    cursor.execute(
        "INSERT INTO dataset_imports (import_id, dataset_id, data_hash, imported_at_utc, "
        "account_count, device_count, account_device_count, transaction_count, "
        "complaint_count, status) VALUES "
        "('IMP001', 'test_dataset_v1', 'hash123', '2026-09-02T12:00:00+00:00', "
        "3, 2, 3, 3, 0, 'SUCCESS');"
    )
    conn.commit()
    cursor.close()

    yield conn
    conn.close()


def test_build_networkx_graph_nodes_and_edges(populated_db: sqlite3.Connection) -> None:
    """Verify MultiDiGraph structure, node types, edge types, and parallel edges."""
    g = build_networkx_graph(populated_db)

    assert isinstance(g, nx.MultiDiGraph)

    # Total nodes = 3 accounts + 2 devices = 5
    assert g.number_of_nodes() == 5
    assert "acc:ACC0001" in g
    assert "acc:ACC0002" in g
    assert "acc:ACC0003" in g
    assert "dev:DEV0001" in g
    assert "dev:DEV0002" in g

    # Check node attributes
    acc1_data = g.nodes["acc:ACC0001"]
    assert acc1_data["node_type"] == "account"
    assert acc1_data["holder_name"] == "Alice"
    assert acc1_data["bank"] == "HDFC"

    dev1_data = g.nodes["dev:DEV0001"]
    assert dev1_data["node_type"] == "device"
    assert dev1_data["device_id"] == "DEV0001"

    # Total edges = 3 account-device links + 3 transactions = 6
    assert g.number_of_edges() == 6

    # Verify parallel transaction edges between acc:ACC0001 and acc:ACC0002
    acc1_acc2_edges = g.get_edge_data("acc:ACC0001", "acc:ACC0002")
    assert acc1_acc2_edges is not None
    assert len(acc1_acc2_edges) == 2  # TXN001 and TXN002
    assert "txn:TXN001" in acc1_acc2_edges
    assert "txn:TXN002" in acc1_acc2_edges
    assert acc1_acc2_edges["txn:TXN001"]["amount_paise"] == 50000
    assert acc1_acc2_edges["txn:TXN002"]["amount_paise"] == 25000

    # Verify account -> device edge
    link_data = g.get_edge_data("acc:ACC0001", "dev:DEV0001")
    assert link_data is not None
    assert "link:ACC0001_DEV0001" in link_data
    assert link_data["link:ACC0001_DEV0001"]["edge_type"] == "uses_device"


def test_build_networkx_graph_status_filter(populated_db: sqlite3.Connection) -> None:
    """Verify transaction status filter excludes non-matching transactions."""
    g = build_networkx_graph(populated_db, status="SUCCESS")

    # 3 links + 2 SUCCESS txns = 5 edges
    assert g.number_of_edges() == 5
    txn_edges = [
        attrs for _, _, attrs in g.edges(data=True) if attrs.get("edge_type") == "transaction"
    ]
    assert len(txn_edges) == 2
    for e in txn_edges:
        assert e["status"] == "SUCCESS"


def test_build_networkx_graph_limit(populated_db: sqlite3.Connection) -> None:
    """Verify limit restricts transaction edges count."""
    g = build_networkx_graph(populated_db, limit=1)

    # 3 links + 1 limited txn = 4 edges
    txn_edges = [
        attrs for _, _, attrs in g.edges(data=True) if attrs.get("edge_type") == "transaction"
    ]
    assert len(txn_edges) == 1


def test_export_cytoscape_json(populated_db: sqlite3.Connection) -> None:
    """Verify Cytoscape.js conversion produces valid schema and accurate metadata."""
    res = get_graph_data(populated_db)

    assert len(res.nodes) == 5
    assert len(res.edges) == 6
    assert res.metadata.dataset_id == "test_dataset_v1"
    assert res.metadata.node_count == 5
    assert res.metadata.edge_count == 6
    assert res.metadata.account_node_count == 3
    assert res.metadata.device_node_count == 2
    assert res.metadata.transaction_edge_count == 3
    assert res.metadata.device_edge_count == 3

    # Check node structure
    sample_node = res.nodes[0]
    assert hasattr(sample_node, "data")
    assert sample_node.data.id.startswith("acc:") or sample_node.data.id.startswith("dev:")

    # Check edge structure
    sample_edge = res.edges[0]
    assert hasattr(sample_edge, "data")
    assert sample_edge.data.source is not None
    assert sample_edge.data.target is not None


def test_get_graph_endpoint_success(populated_db: sqlite3.Connection) -> None:
    """Test GET /api/graph with dependency override."""

    def override_get_db():
        yield populated_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/graph")
        assert response.status_code == 200, response.json()
        payload = response.json()

        assert "nodes" in payload
        assert "edges" in payload
        assert "metadata" in payload
        assert payload["metadata"]["node_count"] == 5
        assert payload["metadata"]["edge_count"] == 6

        # With status filter
        resp_filtered = client.get("/api/graph?status=SUCCESS")
        assert resp_filtered.status_code == 200
        payload_filtered = resp_filtered.json()
        assert payload_filtered["metadata"]["transaction_edge_count"] == 2

        # With limit
        resp_limit = client.get("/api/graph?limit=1")
        assert resp_limit.status_code == 200
        payload_limit = resp_limit.json()
        assert payload_limit["metadata"]["transaction_edge_count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_get_graph_endpoint_db_unavailable() -> None:
    """Test GET /api/graph returns 503 when Turso connection fails."""
    with patch(
        "app.api.routes.graph.get_turso_connection",
        side_effect=Exception("Connection refused"),
    ):
        response = client.get("/api/graph")
        assert response.status_code == 503
        assert "Database connection unavailable" in response.json()["detail"]
