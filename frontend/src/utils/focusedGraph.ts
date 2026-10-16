/**
 * Focused Graph Extractor for Anvik Fraud-Ring Investigator
 * Presentation filter providing a clean, clutter-free 4–5 node demo view.
 * Strictly preserves real backend IDs, transaction amounts, timestamps, and scores.
 */

import { GraphNodeData, GraphEdgeData } from '../types';

export interface FocusedGraphResult {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
  isFocused: boolean;
  scenarioTitle: string;
  scenarioDescription: string;
}

// Canonical syndicate IDs from verified live Turso dataset for CMP0004
export const CANONICAL_DEMO_5_NODES = [
  'acc:ACC0125', // Reported Victim (Origin)
  'acc:ACC0135', // Primary Beneficiary & Rapid Onward Mule
  'acc:ACC0140', // Syndicate Collector Hub
  'acc:ACC0131', // Co-feeder Mule 2
  'acc:ACC0132', // Co-feeder Mule 3
];

// Fallback IDs for mock 9-node network
export const MOCK_DEMO_5_NODES = [
  'ACC_VICTIM_1',
  'ACC_PRIMARY_MULE',
  'ACC_MULE_2',
  'ACC_MULE_3',
  'MERCH_CASHOUT',
];

/**
 * Deterministic layout coordinates for the 5-node focused view (Left-to-Right Money Flow)
 * Avoids layout jitter, overlapping labels, and continuous recalculation.
 */
export const FOCUSED_LAYOUT_COORDINATES: Record<string, { x: number; y: number }> = {
  // Live dataset nodes
  'acc:ACC0125': { x: 140, y: 260 }, // Victim Origin (Left)
  'acc:ACC0135': { x: 380, y: 150 }, // Primary Mule (Center-Top)
  'acc:ACC0131': { x: 380, y: 270 }, // Co-Mule 2 (Center-Middle)
  'acc:ACC0132': { x: 380, y: 390 }, // Co-Mule 3 (Center-Bottom)
  'acc:ACC0140': { x: 660, y: 270 }, // Syndicate Collector Hub (Right)

  // Mock dataset nodes
  'ACC_VICTIM_1': { x: 140, y: 260 },
  'ACC_PRIMARY_MULE': { x: 380, y: 150 },
  'ACC_MULE_2': { x: 380, y: 270 },
  'ACC_MULE_3': { x: 380, y: 390 },
  'MERCH_CASHOUT': { x: 660, y: 270 },
};

/**
 * Extracts a presentation-friendly 4–5 node focused subgraph from the complete network.
 * 
 * Rules:
 * - Maximum 5 visible nodes.
 * - Always preserves real backend node and edge objects without fabrication.
 * - Prioritizes the reported transaction and rapid onward transfer path.
 */
export function getFocusedDemoSubgraph(
  allNodes: GraphNodeData[],
  allEdges: GraphEdgeData[],
  options?: {
    targetId?: string | null;
    maxNodes?: number;
  }
): FocusedGraphResult {
  const maxNodes = Math.min(Math.max(options?.maxNodes || 5, 2), 5); // Strictly clamped to <= 5
  const rawTargetId = options?.targetId?.trim();
  const targetId = rawTargetId
    ? rawTargetId.startsWith('acc:')
      ? rawTargetId
      : `acc:${rawTargetId}`
    : null;

  // Detect if live dataset nodes are present
  const nodeMap = new Map<string, GraphNodeData>();
  for (const n of allNodes) {
    nodeMap.set(n.id, n);
    if (n.accountNo) {
      nodeMap.set(`acc:${n.accountNo}`, n);
      nodeMap.set(n.accountNo, n);
    }
  }

  // 1. Check if canonical live demo scenario nodes are present
  const hasLiveDemoNodes = CANONICAL_DEMO_5_NODES.every((id) => nodeMap.has(id));
  const isTargetingDemo = !targetId || targetId === 'acc:ACC0135' || targetId === 'acc:ACC0125' || targetId === 'acc:ACC0140';

  let selectedNodeIds: string[] = [];

  if (hasLiveDemoNodes && isTargetingDemo) {
    selectedNodeIds = CANONICAL_DEMO_5_NODES.slice(0, maxNodes);
  } else {
    // Check mock demo scenario
    const hasMockDemoNodes = MOCK_DEMO_5_NODES.every((id) => nodeMap.has(id));
    if (hasMockDemoNodes && (!targetId || targetId === 'ACC_PRIMARY_MULE' || targetId === 'ACC_VICTIM_1')) {
      selectedNodeIds = MOCK_DEMO_5_NODES.slice(0, maxNodes);
    } else {
      // Dynamic neighborhood extraction capped at maxNodes (5)
      const centerNode = targetId ? (nodeMap.get(targetId) || allNodes[0]) : allNodes[0];
      if (!centerNode) {
        return {
          nodes: [],
          edges: [],
          isFocused: true,
          scenarioTitle: 'Focused demo view · 5 nodes max',
          scenarioDescription: 'No graph records available.',
        };
      }

      const collected = new Set<string>([centerNode.id]);

      // Priority 1: Connected transaction edges (inflows & outflows)
      const directTxnEdges = allEdges.filter(
        (e) => (e.source === centerNode.id || e.target === centerNode.id) && e.channel === 'UPI_P2P'
      );

      // Sort by amount descending to show significant flows
      directTxnEdges.sort((a, b) => (b.amount || 0) - (a.amount || 0));

      for (const edge of directTxnEdges) {
        if (collected.size >= maxNodes) break;
        const neighbor = edge.source === centerNode.id ? edge.target : edge.source;
        if (nodeMap.has(neighbor)) {
          collected.add(neighbor);
        }
      }

      // Priority 2: 2-hop downstream if space remains
      if (collected.size < maxNodes) {
        for (const firstHop of Array.from(collected)) {
          if (collected.size >= maxNodes) break;
          const downstreamEdges = allEdges.filter((e) => e.source === firstHop && e.channel === 'UPI_P2P');
          for (const edge of downstreamEdges) {
            if (collected.size >= maxNodes) break;
            if (nodeMap.has(edge.target)) {
              collected.add(edge.target);
            }
          }
        }
      }

      selectedNodeIds = Array.from(collected).slice(0, maxNodes);
    }
  }

  const selectedSet = new Set(selectedNodeIds);
  const selectedNodes = selectedNodeIds
    .map((id) => nodeMap.get(id))
    .filter((n): n is GraphNodeData => Boolean(n));

  // Filter edges: only transaction edges connecting the selected nodes
  // Excludes device links in focused account-only view to eliminate visual clutter
  const selectedEdges = allEdges.filter(
    (e) => selectedSet.has(e.source) && selectedSet.has(e.target) && e.channel === 'UPI_P2P'
  );

  return {
    nodes: selectedNodes,
    edges: selectedEdges,
    isFocused: true,
    scenarioTitle: 'Focused demo view · 5 nodes max',
    scenarioDescription: 'Verified 5-node money trail: Disputed transfer from Victim ACC0125 onwards through Mule ACC0135 to Collector Hub ACC0140.',
  };
}
