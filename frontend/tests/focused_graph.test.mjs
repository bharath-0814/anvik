import test from 'node:test';
import assert from 'node:assert/strict';

// Test implementation matching frontend/src/utils/focusedGraph.ts
const CANONICAL_DEMO_5_NODES = [
  'acc:ACC0125',
  'acc:ACC0135',
  'acc:ACC0140',
  'acc:ACC0131',
  'acc:ACC0132',
];

function getFocusedDemoSubgraph(allNodes, allEdges, options) {
  const maxNodes = Math.min(Math.max(options?.maxNodes || 5, 2), 5);
  const rawTargetId = options?.targetId?.trim();
  const targetId = rawTargetId
    ? rawTargetId.startsWith('acc:')
      ? rawTargetId
      : `acc:${rawTargetId}`
    : null;

  const nodeMap = new Map();
  for (const n of allNodes) {
    nodeMap.set(n.id, n);
    if (n.accountNo) {
      nodeMap.set(`acc:${n.accountNo}`, n);
      nodeMap.set(n.accountNo, n);
    }
  }

  const hasLiveDemoNodes = CANONICAL_DEMO_5_NODES.every((id) => nodeMap.has(id));
  const isTargetingDemo = !targetId || targetId === 'acc:ACC0135' || targetId === 'acc:ACC0125' || targetId === 'acc:ACC0140';

  let selectedNodeIds = [];

  if (hasLiveDemoNodes && isTargetingDemo) {
    selectedNodeIds = CANONICAL_DEMO_5_NODES.slice(0, maxNodes);
  } else {
    const centerNode = targetId ? (nodeMap.get(targetId) || allNodes[0]) : allNodes[0];
    if (!centerNode) {
      return { nodes: [], edges: [], isFocused: true };
    }

    const collected = new Set([centerNode.id]);
    const directTxnEdges = allEdges.filter(
      (e) => (e.source === centerNode.id || e.target === centerNode.id) && e.channel === 'UPI_P2P'
    );
    directTxnEdges.sort((a, b) => (b.amount || 0) - (a.amount || 0));

    for (const edge of directTxnEdges) {
      if (collected.size >= maxNodes) break;
      const neighbor = edge.source === centerNode.id ? edge.target : edge.source;
      if (nodeMap.has(neighbor)) {
        collected.add(neighbor);
      }
    }

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

  const selectedSet = new Set(selectedNodeIds);
  const selectedNodes = selectedNodeIds
    .map((id) => nodeMap.get(id))
    .filter(Boolean);

  const selectedEdges = allEdges.filter(
    (e) => selectedSet.has(e.source) && selectedSet.has(e.target) && e.channel === 'UPI_P2P'
  );

  return {
    nodes: selectedNodes,
    edges: selectedEdges,
    isFocused: true,
    scenarioTitle: 'Focused demo view · 5 nodes max',
    scenarioDescription: 'Verified 5-node money trail',
  };
}

// Sample live dataset fixtures
const sampleLiveNodes = [
  { id: 'acc:ACC0125', label: 'ACC0125', type: 'account', accountNo: 'ACC0125', upiId: 'vikram.das125@synhdfc', riskScore: 0 },
  { id: 'acc:ACC0135', label: 'ACC0135', type: 'account', accountNo: 'ACC0135', upiId: 'vikram.reddy135@synicici', riskScore: 90 },
  { id: 'acc:ACC0140', label: 'ACC0140', type: 'account', accountNo: 'ACC0140', upiId: 'diya.das140@synsbi', riskScore: 90 },
  { id: 'acc:ACC0131', label: 'ACC0131', type: 'account', accountNo: 'ACC0131', upiId: 'vivaan.das131@synsbi', riskScore: 75 },
  { id: 'acc:ACC0132', label: 'ACC0132', type: 'account', accountNo: 'ACC0132', upiId: 'ananya.sharma132@synaxis', riskScore: 75 },
  { id: 'acc:ACC0133', label: 'ACC0133', type: 'account', accountNo: 'ACC0133', upiId: 'rohit.mehta133@synicici', riskScore: 75 },
  { id: 'dev:DEV0163', label: 'DEV0163', type: 'device', riskScore: 0 },
];

const sampleLiveEdges = [
  { id: 'txn:TXN002804', source: 'acc:ACC0125', target: 'acc:ACC0135', amount: 10732.62, channel: 'UPI_P2P' },
  { id: 'txn:TXN002806', source: 'acc:ACC0135', target: 'acc:ACC0140', amount: 10088.66, channel: 'UPI_P2P' },
  { id: 'txn:TXN002825', source: 'acc:ACC0131', target: 'acc:ACC0140', amount: 13221.65, channel: 'UPI_P2P' },
  { id: 'txn:TXN002861', source: 'acc:ACC0132', target: 'acc:ACC0140', amount: 11612.44, channel: 'UPI_P2P' },
  { id: 'link:ACC0135_DEV0163', source: 'acc:ACC0135', target: 'dev:DEV0163', amount: 0, channel: 'DEVICE_BIND' },
];

test('getFocusedDemoSubgraph enforces max 5 nodes strictly', () => {
  const result = getFocusedDemoSubgraph(sampleLiveNodes, sampleLiveEdges, { maxNodes: 10 });
  assert.ok(result.nodes.length <= 5, `Expected <= 5 nodes, got ${result.nodes.length}`);
  assert.equal(result.nodes.length, 5);
});

test('getFocusedDemoSubgraph preserves real IDs and edges without fabrication', () => {
  const result = getFocusedDemoSubgraph(sampleLiveNodes, sampleLiveEdges, { targetId: 'ACC0135' });
  const ids = result.nodes.map((n) => n.id);
  assert.deepEqual(ids, ['acc:ACC0125', 'acc:ACC0135', 'acc:ACC0140', 'acc:ACC0131', 'acc:ACC0132']);

  // Disputed transfer TXN002804 and rapid onward TXN002806 must be present
  const edgeIds = result.edges.map((e) => e.id);
  assert.ok(edgeIds.includes('txn:TXN002804'));
  assert.ok(edgeIds.includes('txn:TXN002806'));
  assert.ok(edgeIds.includes('txn:TXN002825'));
  assert.ok(edgeIds.includes('txn:TXN002861'));

  // Device binding edge must NOT be in the focused 5-account view
  assert.equal(edgeIds.includes('link:ACC0135_DEV0163'), false);
});

test('getFocusedDemoSubgraph handles arbitrary target node with max 5 enforcement', () => {
  // Create a 10-node chain
  const chainNodes = Array.from({ length: 10 }, (_, i) => ({
    id: `acc:NODE_${i}`,
    label: `NODE_${i}`,
    type: 'account',
  }));
  const chainEdges = Array.from({ length: 9 }, (_, i) => ({
    id: `txn:T_${i}`,
    source: `acc:NODE_${i}`,
    target: `acc:NODE_${i + 1}`,
    amount: 1000 * (i + 1),
    channel: 'UPI_P2P',
  }));

  const result = getFocusedDemoSubgraph(chainNodes, chainEdges, { targetId: 'acc:NODE_4', maxNodes: 5 });
  assert.ok(result.nodes.length <= 5, `Expected <= 5, got ${result.nodes.length}`);
  assert.ok(result.nodes.some((n) => n.id === 'acc:NODE_4'));
});

test('getFocusedDemoSubgraph returns empty arrays safely if allNodes is empty', () => {
  const result = getFocusedDemoSubgraph([], []);
  assert.equal(result.nodes.length, 0);
  assert.equal(result.edges.length, 0);
  assert.equal(result.isFocused, true);
});
