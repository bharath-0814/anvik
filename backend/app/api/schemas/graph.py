"""Pydantic schemas for Cytoscape.js compatible graph responses."""

from typing import Optional

from pydantic import BaseModel, Field


class NodeData(BaseModel):
    """Payload attributes for a graph node."""

    id: str = Field(..., description="Unique node ID with prefix, e.g. acc:ACC0001 or dev:DEV0001")
    label: str = Field(..., description="Display label for visualization")
    node_type: str = Field(..., description="'account' or 'device'")
    account_id: Optional[str] = None
    holder_name: Optional[str] = None
    vpa: Optional[str] = None
    bank: Optional[str] = None
    device_id: Optional[str] = None


class GraphNode(BaseModel):
    """Cytoscape.js node object wrapper."""

    data: NodeData


class EdgeData(BaseModel):
    """Payload attributes for a graph edge."""

    id: str = Field(..., description="Unique edge ID, e.g. txn:TXN000001 or link:ACC0001_DEV0001")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: str = Field(..., description="'transaction' or 'uses_device'")
    txn_id: Optional[str] = None
    amount_paise: Optional[int] = None
    amount_inr: Optional[float] = None
    timestamp_utc: Optional[str] = None
    raw_timestamp: Optional[str] = None
    txn_type: Optional[str] = None
    status: Optional[str] = None
    device_id: Optional[str] = None


class GraphEdge(BaseModel):
    """Cytoscape.js edge object wrapper."""

    data: EdgeData


class GraphMetadata(BaseModel):
    """Statistical and provenance metadata for graph response."""

    dataset_id: str
    node_count: int
    edge_count: int
    account_node_count: int
    device_node_count: int
    transaction_edge_count: int
    device_edge_count: int
    generated_at_utc: str


class GraphResponse(BaseModel):
    """Full Cytoscape.js compliant graph response."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: GraphMetadata
