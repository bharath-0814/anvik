/**
 * Anvik API Service Client
 * Connects frontend to the Anvik FastAPI / NetworkX backend.
 */

import { GraphNodeData, GraphEdgeData, ComplaintRecord, NodeRole } from '../types';

// Resolve base URL from Vite environment variable or default to production Vercel backend
export const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL || 'https://anvik-backend.vercel.app'
).replace(/\/+$/, '');

export interface BackendNodeData {
  id: string;
  label: string;
  node_type: 'account' | 'device';
  account_id?: string | null;
  holder_name?: string | null;
  vpa?: string | null;
  bank?: string | null;
  device_id?: string | null;
}

export interface BackendGraphNode {
  data: BackendNodeData;
}

export interface BackendEdgeData {
  id: string;
  source: string;
  target: string;
  edge_type: 'transaction' | 'uses_device';
  txn_id?: string | null;
  amount_paise?: number | null;
  amount_inr?: number | null;
  timestamp_utc?: string | null;
  raw_timestamp?: string | null;
  txn_type?: string | null;
  status?: string | null;
  device_id?: string | null;
}

export interface BackendGraphEdge {
  data: BackendEdgeData;
}

export interface BackendGraphMetadata {
  dataset_id: string;
  node_count: number;
  edge_count: number;
  account_node_count: number;
  device_node_count: number;
  transaction_edge_count: number;
  device_edge_count: number;
  generated_at_utc: string;
}

export interface BackendGraphResponse {
  nodes: BackendGraphNode[];
  edges: BackendGraphEdge[];
  metadata: BackendGraphMetadata;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ReadyResponse {
  status: string;
  database: {
    connected: boolean;
    message: string;
  };
  environment: string;
}

export interface GraphFilters {
  status?: string;
  limit?: number;
}

export interface BackendComplaintItem {
  complaint_id: string;
  victim_account_id: string;
  victim_vpa: string;
  txn_id: string;
  amount_inr?: number | null;
  beneficiary_account_id?: string | null;
  beneficiary_vpa?: string | null;
  complaint_date?: string | null;
  status: string;
}

export interface BackendComplaintsResponse {
  total_count: number;
  complaints: BackendComplaintItem[];
}

export interface BackendAlertItem {
  alert_id: string;
  rule_id: string;
  title: string;
  priority: 'high' | 'medium' | 'low';
  score: number;
  created_at: string;
  account_ids: string[];
  vpas: string[];
  txn_ids: string[];
  linked_txn_ids: string[];
  evidence: Record<string, any>;
  explanation: string;
  limitations: string;
  alternative_explanations: string[];
  would_clear_if: string[];
  complaint_ids: string[];
  related_alert_ids: string[];
  ring_id?: string | null;
  informational_only: boolean;
}

export interface BackendRingItem {
  ring_id: string;
  account_ids: string[];
  alert_ids: string[];
  highest_priority: 'high' | 'medium' | 'low';
  highest_score?: number | null;
}

export interface BackendAlertsResponse {
  dataset_id: string;
  generated_at: string;
  amount_unit: string;
  count: number;
  meta: Record<string, any>;
  alerts: BackendAlertItem[];
  rings: BackendRingItem[];
  account_summaries: Array<{
    account_id: string;
    alert_ids: string[];
    highest_priority: 'high' | 'medium' | 'low';
    highest_score?: number | null;
  }>;
}

export interface AlertFilters {
  rule_id?: string;
  priority?: string;
  account_id?: string;
  txn_id?: string;
}

/**
 * Health check probe (liveness)
 */
export async function getHealth(): Promise<HealthResponse> {
  const url = `${API_BASE_URL}/api/health`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Health check failed with HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Database readiness probe
 */
export async function getReady(): Promise<ReadyResponse> {
  const url = `${API_BASE_URL}/api/ready`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Readiness probe failed with HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch network graph topology from backend
 */
export async function getGraph(filters?: GraphFilters): Promise<BackendGraphResponse> {
  const params = new URLSearchParams();
  if (filters?.status) {
    params.set('status', filters.status);
  }
  if (filters?.limit && filters.limit > 0) {
    params.set('limit', String(filters.limit));
  }

  const queryString = params.toString();
  const url = `${API_BASE_URL}/api/graph${queryString ? `?${queryString}` : ''}`;

  const res = await fetch(url);
  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to fetch graph (HTTP ${res.status}): ${errorText || res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch preloaded synthetic complaints from backend
 */
export async function getComplaints(accountId?: string): Promise<BackendComplaintsResponse> {
  const params = new URLSearchParams();
  if (accountId) {
    params.set('account_id', accountId);
  }

  const queryString = params.toString();
  const url = `${API_BASE_URL}/api/complaints${queryString ? `?${queryString}` : ''}`;

  const res = await fetch(url);
  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to fetch complaints (HTTP ${res.status}): ${errorText || res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch fraud-pattern alerts and ring clusters from backend (Aryan contract)
 */
export async function getAlerts(filters?: AlertFilters): Promise<BackendAlertsResponse> {
  const params = new URLSearchParams();
  if (filters?.rule_id) params.set('rule_id', filters.rule_id);
  if (filters?.priority) params.set('priority', filters.priority);
  if (filters?.account_id) params.set('account_id', filters.account_id);
  if (filters?.txn_id) params.set('txn_id', filters.txn_id);

  const queryString = params.toString();
  const url = `${API_BASE_URL}/api/alerts${queryString ? `?${queryString}` : ''}`;

  const res = await fetch(url);
  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to fetch alerts (HTTP ${res.status}): ${errorText || res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch a specific transaction by transaction ID
 */
export async function getTransaction(txnId: string): Promise<any> {
  const cleanTxnId = (txnId || '').trim();
  const url = `${API_BASE_URL}/api/transactions/${encodeURIComponent(cleanTxnId)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to fetch transaction ${txnId} (HTTP ${res.status}): ${errorText || res.statusText}`);
  }
  return res.json();
}

/**
 * Adapt backend complaint record to frontend ComplaintRecord
 */
export function adaptBackendComplaintToRecord(item: BackendComplaintItem): ComplaintRecord {
  const dateFormatted = item.complaint_date
    ? new Date(item.complaint_date).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : '15 Oct 2026';

  return {
    id: item.complaint_id,
    complaintRef: `NCRP-${item.complaint_id}`,
    date: dateFormatted,
    shortDescription: `Disputed transfer of ₹${(item.amount_inr || 0).toLocaleString('en-IN')} to ${
      item.beneficiary_vpa || item.beneficiary_account_id || 'unlinked beneficiary'
    }`,
    category: 'UPI Dispute',
    disputeAmount: item.amount_inr || 0,
    relatedAccountId: item.victim_account_id,
    relatedAccountUpi: item.victim_vpa,
    relatedBeneficiaryUpi: item.beneficiary_vpa || undefined,
    relatedBeneficiaryAccountId: item.beneficiary_account_id || undefined,
    relatedTxnUtr: item.txn_id,
    riskLevel: 'HIGH',
    status: 'under_investigation',
    analystNotes: `Reported synthetic complaint against transaction ${item.txn_id}. Beneficiary: ${
      item.beneficiary_account_id || 'unknown'
    }.`,
  };
}

/**
 * Enrich an array of GraphNodeData with risk scores and roles from account summaries
 */
export function enrichNodesWithAlertSummaries(
  nodes: GraphNodeData[],
  accountSummaries?: BackendAlertsResponse['account_summaries']
): GraphNodeData[] {
  if (!accountSummaries || !accountSummaries.length) return nodes;

  const summaryMap = new Map<string, (typeof accountSummaries)[0]>();
  for (const s of accountSummaries) {
    if (s.account_id) {
      const rawId = s.account_id;
      summaryMap.set(rawId, s);
      summaryMap.set(rawId.toUpperCase(), s);
      summaryMap.set(rawId.toLowerCase(), s);

      if (!rawId.startsWith('acc:')) {
        summaryMap.set(`acc:${rawId}`, s);
        summaryMap.set(`acc:${rawId.toUpperCase()}`, s);
      } else {
        const stripped = rawId.replace(/^acc:/i, '');
        summaryMap.set(stripped, s);
        summaryMap.set(stripped.toUpperCase(), s);
      }
    }
  }

  return nodes.map((node) => {
    const acctKey = node.accountNo || node.id;
    const summary = summaryMap.get(acctKey) || summaryMap.get(node.id);
    if (!summary) return node;

    const riskScore = Math.round((summary.highest_score || 0) * 100);
    let role = node.role;
    let status = node.status;
    if (summary.highest_priority === 'high' || riskScore >= 70) {
      role = 'aggregator_mule';
      status = 'flagged';
    } else if (summary.highest_priority === 'medium' || riskScore >= 40) {
      role = 'secondary_mule';
      status = 'flagged';
    }

    return {
      ...node,
      riskScore,
      role,
      status,
    };
  });
}

/**
 * Cleanly adapt backend graph elements to frontend UI types.
 * Preserves exact backend IDs (acc:..., dev:..., txn:..., link:...) without fabricated identifiers.
 * Enriches nodes with risk scores and mule roles from account summaries if provided.
 */
export function adaptBackendGraphToFrontend(
  backendData: BackendGraphResponse,
  alertsData?: BackendAlertsResponse | null
): {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
  metadata: BackendGraphMetadata;
} {
  // Build lookup index from alerts account_summaries if available
  const summaryMap = new Map<
    string,
    {
      account_id: string;
      alert_ids: string[];
      highest_priority: 'high' | 'medium' | 'low';
      highest_score?: number | null;
    }
  >();

  if (alertsData?.account_summaries?.length) {
    for (const summary of alertsData.account_summaries) {
      if (summary.account_id) {
        const rawId = summary.account_id;
        summaryMap.set(rawId, summary);
        summaryMap.set(rawId.toUpperCase(), summary);
        summaryMap.set(rawId.toLowerCase(), summary);

        if (!rawId.startsWith('acc:')) {
          summaryMap.set(`acc:${rawId}`, summary);
          summaryMap.set(`acc:${rawId.toUpperCase()}`, summary);
        } else {
          const stripped = rawId.replace(/^acc:/i, '');
          summaryMap.set(stripped, summary);
          summaryMap.set(stripped.toUpperCase(), summary);
        }
      }
    }
  }

  const nodes: GraphNodeData[] = (backendData.nodes || []).map((gn) => {
    const d = gn.data;
    const isDevice = d.node_type === 'device';

    // Check account summary for risk score enrichment
    const acctKey = d.account_id || d.id;
    const summary = summaryMap.get(acctKey) || summaryMap.get(d.id);

    let riskScore = 0;
    let role: NodeRole = isDevice ? 'device_farm' : 'verified_control';
    let status: 'active' | 'frozen' | 'flagged' | 'verified' = 'active';

    if (summary) {
      riskScore = Math.round((summary.highest_score || 0) * 100);
      if (summary.highest_priority === 'high' || riskScore >= 70) {
        role = 'aggregator_mule';
        status = 'flagged';
      } else if (summary.highest_priority === 'medium' || riskScore >= 40) {
        role = 'secondary_mule';
        status = 'flagged';
      }
    }

    return {
      id: d.id,
      label: d.label || d.id,
      type: isDevice ? 'device' : 'account',
      role,
      riskScore,
      status,
      subText: isDevice ? (d.device_id || d.label) : (d.bank ? `${d.bank} · ${d.holder_name || ''}` : (d.vpa || '')),
      upiId: d.vpa || undefined,
      bankName: d.bank || undefined,
      deviceId: d.device_id || undefined,
      accountNo: d.account_id || undefined,
    };
  });

  const edges: GraphEdgeData[] = (backendData.edges || []).map((ge) => {
    const d = ge.data;
    const isDeviceLink = d.edge_type === 'uses_device';

    return {
      id: d.id,
      source: d.source,
      target: d.target,
      amount: d.amount_inr || 0,
      timestamp: d.raw_timestamp || d.timestamp_utc || '',
      utr: d.txn_id || d.id,
      channel: isDeviceLink ? 'DEVICE_BIND' : 'UPI_P2P',
      isSuspicious: false,
      ruleTriggered: undefined,
    };
  });

  return {
    nodes,
    edges,
    metadata: backendData.metadata,
  };
}
