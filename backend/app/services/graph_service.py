"""Graph construction service using NetworkX and Cytoscape.js export."""

from datetime import datetime, timezone
from typing import Any, Optional

import networkx as nx

from app.api.schemas.graph import (
    EdgeData,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    GraphResponse,
    NodeData,
)
from app.db.repository import (
    get_account_devices,
    get_accounts,
    get_devices,
    get_latest_import,
    get_transactions,
)


def build_networkx_graph(
    conn: Any,
    status: Optional[str] = None,
    limit: Optional[int] = None,
) -> nx.MultiDiGraph:
    """Build a NetworkX MultiDiGraph representing accounts, devices, and transactions.

    Nodes:
    - acc:<account_id> with type 'account'
    - dev:<device_id> with type 'device'

    Edges:
    - txn:<txn_id> directed acc:<sender> -> acc:<receiver> with type 'transaction'
    - link:<account_id>_<device_id> directed acc:<account_id> -> dev:<device_id>
      with type 'uses_device'
    """
    g = nx.MultiDiGraph()

    # 1. Accounts
    accounts = get_accounts(conn)
    for acc in accounts:
        node_id = f"acc:{acc['account_id']}"
        g.add_node(
            node_id,
            id=node_id,
            label=acc["account_id"],
            node_type="account",
            account_id=acc["account_id"],
            holder_name=acc.get("holder_name"),
            vpa=acc.get("vpa"),
            bank=acc.get("bank"),
            device_id=None,
        )

    # 2. Devices
    devices = get_devices(conn)
    for dev in devices:
        node_id = f"dev:{dev['device_id']}"
        g.add_node(
            node_id,
            id=node_id,
            label=dev["device_id"],
            node_type="device",
            account_id=None,
            holder_name=None,
            vpa=None,
            bank=None,
            device_id=dev["device_id"],
        )

    # 3. Account -> Device links
    account_devices = get_account_devices(conn)
    for link in account_devices:
        acc_node = f"acc:{link['account_id']}"
        dev_node = f"dev:{link['device_id']}"
        edge_id = f"link:{link['account_id']}_{link['device_id']}"

        if not g.has_node(acc_node):
            g.add_node(
                acc_node,
                id=acc_node,
                label=link["account_id"],
                node_type="account",
                account_id=link["account_id"],
            )
        if not g.has_node(dev_node):
            g.add_node(
                dev_node,
                id=dev_node,
                label=link["device_id"],
                node_type="device",
                device_id=link["device_id"],
            )

        g.add_edge(
            acc_node,
            dev_node,
            key=edge_id,
            id=edge_id,
            source=acc_node,
            target=dev_node,
            edge_type="uses_device",
            device_id=link["device_id"],
        )

    # 4. Transactions (sender -> receiver)
    transactions = get_transactions(conn, status=status, limit=limit)
    for txn in transactions:
        src_node = f"acc:{txn['sender_account_id']}"
        tgt_node = f"acc:{txn['receiver_account_id']}"
        edge_id = f"txn:{txn['txn_id']}"

        if not g.has_node(src_node):
            g.add_node(
                src_node,
                id=src_node,
                label=txn["sender_account_id"],
                node_type="account",
                account_id=txn["sender_account_id"],
            )
        if not g.has_node(tgt_node):
            g.add_node(
                tgt_node,
                id=tgt_node,
                label=txn["receiver_account_id"],
                node_type="account",
                account_id=txn["receiver_account_id"],
            )

        g.add_edge(
            src_node,
            tgt_node,
            key=edge_id,
            id=edge_id,
            source=src_node,
            target=tgt_node,
            edge_type="transaction",
            txn_id=txn["txn_id"],
            amount_paise=txn.get("amount_paise"),
            amount_inr=txn.get("amount_inr"),
            timestamp_utc=txn.get("timestamp_utc"),
            raw_timestamp=txn.get("raw_timestamp"),
            txn_type=txn.get("txn_type"),
            status=txn.get("status"),
            device_id=txn.get("device_id"),
        )

    return g


def export_cytoscape_json(
    g: nx.MultiDiGraph,
    dataset_id: str = "shivam_dataset_v1",
) -> GraphResponse:
    """Transform a NetworkX graph into Cytoscape.js compatible response payload."""
    nodes: list[GraphNode] = []
    account_node_count = 0
    device_node_count = 0

    for _node_id, attrs in g.nodes(data=True):
        node_data = NodeData(
            id=attrs["id"],
            label=attrs.get("label", attrs["id"]),
            node_type=attrs.get("node_type", "account"),
            account_id=attrs.get("account_id"),
            holder_name=attrs.get("holder_name"),
            vpa=attrs.get("vpa"),
            bank=attrs.get("bank"),
            device_id=attrs.get("device_id"),
        )
        nodes.append(GraphNode(data=node_data))
        if attrs.get("node_type") == "account":
            account_node_count += 1
        elif attrs.get("node_type") == "device":
            device_node_count += 1

    edges: list[GraphEdge] = []
    transaction_edge_count = 0
    device_edge_count = 0

    for _u, _v, _key, attrs in g.edges(data=True, keys=True):
        edge_data = EdgeData(
            id=attrs["id"],
            source=attrs["source"],
            target=attrs["target"],
            edge_type=attrs.get("edge_type", "transaction"),
            txn_id=attrs.get("txn_id"),
            amount_paise=attrs.get("amount_paise"),
            amount_inr=attrs.get("amount_inr"),
            timestamp_utc=attrs.get("timestamp_utc"),
            raw_timestamp=attrs.get("raw_timestamp"),
            txn_type=attrs.get("txn_type"),
            status=attrs.get("status"),
            device_id=attrs.get("device_id"),
        )
        edges.append(GraphEdge(data=edge_data))
        if attrs.get("edge_type") == "transaction":
            transaction_edge_count += 1
        elif attrs.get("edge_type") == "uses_device":
            device_edge_count += 1

    metadata = GraphMetadata(
        dataset_id=dataset_id,
        node_count=len(nodes),
        edge_count=len(edges),
        account_node_count=account_node_count,
        device_node_count=device_node_count,
        transaction_edge_count=transaction_edge_count,
        device_edge_count=device_edge_count,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )

    return GraphResponse(nodes=nodes, edges=edges, metadata=metadata)


def get_graph_data(
    conn: Any,
    status: Optional[str] = None,
    limit: Optional[int] = None,
) -> GraphResponse:
    """Fetch data from repository, build graph, and return Cytoscape.js response."""
    latest_import = get_latest_import(conn)
    dataset_id = latest_import["dataset_id"] if latest_import else "shivam_dataset_v1"
    g = build_networkx_graph(conn, status=status, limit=limit)
    return export_cytoscape_json(g, dataset_id=dataset_id)
