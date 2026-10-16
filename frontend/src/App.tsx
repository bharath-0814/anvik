import React, { useState, useMemo, useRef, useEffect } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { LoginPage } from './components/LoginPage';
import { Header } from './components/Header';
import { Sidebar, LeftNavDrawer } from './components/Sidebar';
import { NetworkGraphCanvas } from './components/NetworkGraphCanvas';
import { TransactionTimelineBar } from './components/TransactionTimelineBar';
import { InvestigationInsightsRail } from './components/InvestigationInsightsRail';
import { InvestigationIntakeScreen } from './components/InvestigationIntakeScreen';
import { TraceConnectionsScreen } from './components/TraceConnectionsScreen';
import { ComplaintsPanel } from './components/ComplaintsPanel';
import { FraudTimelinePanel } from './components/FraudTimelinePanel';
import { InvestigationSummaryPanel } from './components/InvestigationSummaryPanel';
import { FilterSlidebar } from './components/FilterSlidebar';
import { ComplaintIntakeModal } from './components/ComplaintIntakeModal';
import { downloadInvestigationReport } from './utils/reportGenerator';
import { 
  getGraph, 
  getHealth, 
  getComplaints,
  getAlerts,
  adaptBackendGraphToFrontend, 
  adaptBackendComplaintToRecord,
  BackendGraphMetadata, 
  BackendAlertItem,
  API_BASE_URL 
} from './services/api';
import { 
  NETWORK_9_NODES, 
  NETWORK_9_EDGES, 
  NetworkNode, 
  NetworkEdge 
} from './mock/network9Data';
import { getCaseInvestigationData } from './mock/caseData';
import { 
  SYNTHETIC_NODES, 
  SYNTHETIC_EDGES, 
  SYNTHETIC_TIMELINE, 
  DEMO_COMPLAINTS 
} from './mock/syntheticData';
import { 
  GraphNodeData, 
  GraphEdgeData, 
  ComplaintRecord, 
  ComplaintStatus, 
  TimelineEvent 
} from './types';
import { 
  X, 
  Network, 
  SlidersHorizontal, 
  ArrowLeftRight, 
  Activity, 
  ChevronLeft,
  Database,
  RefreshCw,
  AlertTriangle,
  Radio,
  Sparkles,
  Layers
} from 'lucide-react';

type WorkspaceStage = 'complaints' | 'trace' | 'investigation';

function DashboardContent() {
  // Authentication State: Login Page is Stage 1 (The VERY FIRST SCREEN)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [analystGovtId, setAnalystGovtId] = useState<string>('LEA-IND-8812');

  const handleLogin = (govtId: string) => {
    setAnalystGovtId(govtId);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setWorkspaceStage('complaints');
    setIsGraphVisible(false);
  };

  // Investigation Navigation Stages: complaints -> trace -> investigation
  const [workspaceStage, setWorkspaceStage] = useState<WorkspaceStage>('complaints');
  const [activeCaseId, setActiveCaseId] = useState('NCRP-2026-0839');
  const [activeTxnId, setActiveTxnId] = useState('UPI260915083902');
  const [activeDevId, setActiveDevId] = useState('ANDR_09F2');
  const [isLoadingGraph, setIsLoadingGraph] = useState(false);

  // Interactive Graph Visibility & Partial Text Side Panel Slider State
  const [isGraphVisible, setIsGraphVisible] = useState<boolean>(false);
  const [isTextPanelOpen, setIsTextPanelOpen] = useState<boolean>(true); // Slider toggle for partial text side

  // Active Right Drawer ('complaints' | 'timeline' | 'summary' | null)
  const [activeDrawer, setActiveDrawer] = useState<LeftNavDrawer>(null);

  // Search & Filters state
  const [searchQuery, setSearchQuery] = useState('');
  const [minRiskScore, setMinRiskScore] = useState(0);
  const [minAmount, setMinAmount] = useState(0);
  const [timeRange, setTimeRange] = useState('Last 24 hours');
  const [layoutName, setLayoutName] = useState<'cose' | 'concentric' | 'breadthfirst' | 'circle'>('cose');
  const [filterTypes, setFilterTypes] = useState<{ [key: string]: boolean }>({
    account: true,
    device: true,
    merchant: true,
    complaint: true,
  });

  // Slidebars & Modals
  const [isFilterSlidebarOpen, setIsFilterSlidebarOpen] = useState(false);
  const [complaintModalOpen, setComplaintModalOpen] = useState(false);

  // Core Data state
  const [nodes, setNodes] = useState<GraphNodeData[]>(SYNTHETIC_NODES);
  const [edges, setEdges] = useState<GraphEdgeData[]>(SYNTHETIC_EDGES);
  const [timeline] = useState<TimelineEvent[]>(SYNTHETIC_TIMELINE);

  // Live Backend API vs Mock Demo Data State
  const [dataSourceMode, setDataSourceMode] = useState<'live' | 'mock'>('live');
  const [liveNodes, setLiveNodes] = useState<GraphNodeData[]>([]);
  const [liveEdges, setLiveEdges] = useState<GraphEdgeData[]>([]);
  const [liveMetadata, setLiveMetadata] = useState<BackendGraphMetadata | null>(null);
  const [isLiveConnected, setIsLiveConnected] = useState<boolean>(false);
  const [isLoadingLiveGraph, setIsLoadingLiveGraph] = useState<boolean>(false);
  const [liveGraphError, setLiveGraphError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [limitFilter, setLimitFilter] = useState<number>(200);
  const [selectedEntity, setSelectedEntity] = useState<GraphNodeData | null>(null);
  const [liveAlerts, setLiveAlerts] = useState<BackendAlertItem[]>([]);

  // Fetch graph from real FastAPI backend (GET /api/graph)
  const fetchLiveGraph = async (statusParam?: string, limitParam?: number) => {
    setIsLoadingLiveGraph(true);
    setLiveGraphError(null);
    try {
      const filters: { status?: string; limit?: number } = {};
      const s = statusParam !== undefined ? statusParam : statusFilter;
      const l = limitParam !== undefined ? limitParam : limitFilter;
      if (s && s !== 'ALL') filters.status = s;
      if (l && l > 0) filters.limit = l;

      // Fetch graph, alerts, and complaints concurrently
      const [graphRes, alertsRes, complaintsRes] = await Promise.all([
        getGraph(filters),
        getAlerts().catch((err) => {
          console.warn('Backend alerts fetch failed:', err);
          return null;
        }),
        getComplaints().catch((err) => {
          console.warn('Backend complaints fetch failed:', err);
          return null;
        }),
      ]);

      if (alertsRes?.alerts?.length) {
        setLiveAlerts(alertsRes.alerts);
      }

      if (complaintsRes?.complaints?.length) {
        const adaptedComplaints = complaintsRes.complaints.map(adaptBackendComplaintToRecord);
        setComplaints(adaptedComplaints);
      }

      // adaptBackendGraphToFrontend enriches nodes with risk scores from alertsRes
      const adapted = adaptBackendGraphToFrontend(graphRes, alertsRes);
      setLiveNodes(adapted.nodes);
      setLiveEdges(adapted.edges);
      setLiveMetadata(adapted.metadata);
      setIsLiveConnected(true);
      setDataSourceMode('live');
    } catch (err: any) {
      console.warn('Backend API connection check failed:', err);
      setLiveGraphError(err?.message || 'Failed to connect to Anvik backend API');
      setIsLiveConnected(false);
    } finally {
      setIsLoadingLiveGraph(false);
    }
  };

  // Attempt live connection on mount
  useEffect(() => {
    fetchLiveGraph();
  }, []);

  // Case Investigation Dossier & Dynamic Network Data derived from activeCaseId
  const activeCaseData = useMemo(() => getCaseInvestigationData(activeCaseId), [activeCaseId]);
  const networkNodes = useMemo(() => activeCaseData.nodes || NETWORK_9_NODES, [activeCaseData]);
  const networkEdges = useMemo(() => activeCaseData.edges || NETWORK_9_EDGES, [activeCaseData]);
  const [selectedNetworkNode, setSelectedNetworkNode] = useState<NetworkNode | null>(null);
  const [timelineIndex, setTimelineIndex] = useState<number>(4);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Complaints state with LocalStorage persistence
  const [complaints, setComplaints] = useState<ComplaintRecord[]>(() => {
    try {
      const saved = localStorage.getItem('anvik_complaints_data');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn('Could not read complaints from localStorage', e);
    }
    return DEMO_COMPLAINTS;
  });

  // Selection & Freezing state
  const [selectedComplaint, setSelectedComplaint] = useState<ComplaintRecord | null>(null);
  const [selectedTimelineEvent, setSelectedTimelineEvent] = useState<TimelineEvent | null>(null);
  const [frozenNodeIds, setFrozenNodeIds] = useState<Set<string>>(new Set());

  // Download Comprehensive Forensic Investigation Report (Descriptive Analysis + Graph)
  const handleDownloadReport = () => {
    const reportNodes: GraphNodeData[] = networkNodes.map((n) => ({
      id: n.id,
      label: n.name,
      type: n.type === 'upi' || n.type === 'mule' ? 'account' : n.type === 'device' ? 'device' : 'merchant',
      role: n.role as any,
      riskScore: n.riskScore,
      status: n.status,
      upiId: n.handle.includes('@') ? n.handle : undefined,
      deviceId: n.type === 'device' ? n.handle : undefined,
      bankName: n.bank,
      disputeAmount: n.disputeAmount,
    }));

    const reportEdges: GraphEdgeData[] = networkEdges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      amount: e.amount || 0,
      timestamp: `2026-10-15 ${e.timestamp}`,
      utr: `UTR-2026-${e.id.toUpperCase()}`,
      channel: e.type === 'device_link' ? 'DEVICE_BIND' : 'UPI_P2P',
      isSuspicious: e.type === 'transaction' && (e.amount || 0) > 5000,
      ruleTriggered: e.ruleTriggered,
    }));

    downloadInvestigationReport({
      caseId: activeCaseId,
      graphImageBase64: null,
      nodes: reportNodes,
      edges: reportEdges,
      complaints,
      timeline,
      analystName: `Officer ${analystGovtId} (Bharath K - Member 3)`,
    });
  };

  // Step A: When user clicks "Investigate" on a complaint in Complaints & records
  const handleStartTrace = (txnId: string, devId: string, cId: string) => {
    setActiveTxnId(txnId);
    setActiveDevId(devId);
    setActiveCaseId(cId);
    setWorkspaceStage('trace');
  };

  // Step B: When user clicks "Open investigation" on TraceConnectionsScreen
  const handleOpenInvestigation = (txnId: string, devId: string, cId: string) => {
    setIsLoadingGraph(true);
    setActiveTxnId(txnId);
    setActiveDevId(devId);
    setActiveCaseId(cId);
    setTimeout(() => {
      setIsLoadingGraph(false);
      setWorkspaceStage('investigation');
      setIsGraphVisible(false);
    }, 200);
  };

  // Focus on verified demo scenario: Complaint CMP0004 / Txn TXN002804 / Victim ACC0125 -> Beneficiary ACC0135
  const handleSelectDemoScenario = () => {
    setActiveCaseId('CMP0004');
    setActiveTxnId('TXN002804');
    setActiveDevId('DEV0163');
    setWorkspaceStage('investigation');
    setIsGraphVisible(true);
    setIsTextPanelOpen(true);

    const currentNodes = dataSourceMode === 'live' && liveNodes.length > 0 ? liveNodes : nodes;
    const foundNode = currentNodes.find(
      (n) =>
        n.id === 'acc:ACC0135' ||
        n.id === 'ACC0135' ||
        n.accountNo === 'ACC0135' ||
        n.label?.includes('ACC0135')
    );

    const targetNode: GraphNodeData = foundNode || {
      id: 'acc:ACC0135',
      label: 'ACC0135',
      type: 'account',
      role: 'aggregator_mule',
      riskScore: 90,
      status: 'flagged',
      subText: 'ICICI Bank · Vikram Reddy',
      upiId: 'vikram.reddy135@synicici',
      bankName: 'ICICI Bank',
      accountNo: 'ACC0135',
      disputeAmount: 5594.16,
    };

    setSelectedEntity(targetNode);
    setSelectedNetworkNode({
      id: targetNode.id,
      name: 'ACC0135 (Vikram Reddy)',
      handle: targetNode.upiId || 'vikram.reddy135@synicici',
      role: 'Aggregator Mule / Rapid Onward Transfer',
      type: 'mule',
      bank: targetNode.bankName || 'ICICI Bank',
      riskScore: targetNode.riskScore || 90,
      status: 'flagged',
      timestamp: '2026-10-15 10:14 IST',
      x: 0,
      y: 0,
      disputeAmount: 5594.16,
    });
  };

  // Step C: When user clicks "Analysis" in the main interface
  const handleRunAnalysis = () => {
    setIsGraphVisible(true);
    setIsTextPanelOpen(true);
  };

  // Return to Complaints & records feed
  const handleReturnToComplaints = () => {
    setWorkspaceStage('complaints');
    setIsGraphVisible(false);
  };

  // Toggle Left Nav Drawers
  const handleToggleDrawer = (drawer: 'complaints' | 'timeline' | 'summary') => {
    if (activeDrawer === drawer) {
      setActiveDrawer(null);
    } else {
      setActiveDrawer(drawer);
    }
  };

  // Status Updater for Complaints (with LocalStorage write)
  const handleUpdateComplaintStatus = (complaintId: string, newStatus: ComplaintStatus) => {
    setComplaints((prev) => {
      const updated = prev.map((c) =>
        c.id === complaintId ? { ...c, status: newStatus } : c
      );
      try {
        localStorage.setItem('anvik_complaints_data', JSON.stringify(updated));
      } catch (e) {
        console.warn('Could not write complaints to localStorage', e);
      }
      return updated;
    });
  };

  // Complaint selection -> Cross-highlight in network
  const handleSelectComplaint = (cmp: ComplaintRecord | null) => {
    setSelectedComplaint(cmp);
    setSelectedTimelineEvent(null);
    if (!cmp) return;

    if (
      cmp.id === 'CMP0004' ||
      cmp.complaintRef?.includes('CMP0004') ||
      cmp.relatedTxnUtr === 'TXN002804' ||
      cmp.relatedBeneficiaryAccountId === 'ACC0135'
    ) {
      handleSelectDemoScenario();
      return;
    }

    const currentNodes = dataSourceMode === 'live' && liveNodes.length > 0 ? liveNodes : nodes;
    const targetEntity = currentNodes.find(
      (n) =>
        n.id === cmp.relatedAccountId ||
        n.accountNo === cmp.relatedAccountId ||
        n.upiId === cmp.relatedAccountUpi ||
        n.id === `acc:${cmp.relatedAccountId}`
    );
    if (targetEntity) {
      setSelectedEntity(targetEntity);
    }

    const target = networkNodes.find((n) => n.id === cmp.relatedAccountId || n.handle === cmp.relatedAccountUpi);
    if (target) {
      setSelectedNetworkNode(target);
    }
  };

  // Timeline Event selection -> Cross-highlight in network
  const handleSelectTimelineEvent = (evt: TimelineEvent | null) => {
    setSelectedTimelineEvent(evt);
    setSelectedComplaint(null);
    if (evt) {
      const target = networkNodes.find((n) => n.id === evt.sender || n.handle === evt.senderUpi);
      if (target) {
        setSelectedNetworkNode(target);
      }
    }
  };

  // Counterfactual Freeze
  const handleToggleFreeze = (nodeId: string) => {
    setFrozenNodeIds((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  // Add Complaint Modal
  const handleAddComplaint = (newComplaintNode: GraphNodeData, newEdge: GraphEdgeData) => {
    setNodes((prev) => [newComplaintNode, ...prev]);
    setEdges((prev) => [newEdge, ...prev]);
  };

  const resetFilters = () => {
    setMinRiskScore(0);
    setMinAmount(0);
    setTimeRange('Last 24 hours');
    setLayoutName('cose');
    setFilterTypes({ account: true, device: true, merchant: true, complaint: true });
    setSearchQuery('');
  };

  // 1. Stage 1: The very first page shown before anything else is the ANVIK Login Page
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="h-screen w-screen flex flex-col font-sans overflow-hidden bg-[#FBF9F4] text-slate-800">
      {/* 1. Top Header Bar (Brand Logo, Breadcrumbs, Demo Workspace, Controls) */}
      <Header
        currentInvestigationId={activeCaseId}
        isGraphLoaded={workspaceStage === 'investigation'}
        onReturnToIntake={handleReturnToComplaints}
        onOpenSearch={() => setIsFilterSlidebarOpen(true)}
        onOpenAlerts={() => handleToggleDrawer('summary')}
        alertCount={dataSourceMode === 'live' && liveAlerts.length > 0 ? liveAlerts.length : 3}
        onDownloadReport={handleDownloadReport}
        onLogout={handleLogout}
        isLiveConnected={isLiveConnected}
        dataSourceMode={dataSourceMode}
        onSelectDemoScenario={handleSelectDemoScenario}
      />

      {/* 2. Main Investigation Workspace */}
      <div className="flex-1 flex min-h-0 relative overflow-hidden bg-[#FBF9F4]">
        {/* Left Action Rail (Icon-Only buttons with hover text tooltips positioned above graph) */}
        <div className="relative z-50 shrink-0 h-full">
          <Sidebar
            activeDrawer={activeDrawer}
            onToggleDrawer={handleToggleDrawer}
            complaintCount={complaints.length}
          />
        </div>

        {/* Stage 2: Complaints & Records case selection screen (Appears directly after Login) */}
        {workspaceStage === 'complaints' && (
          <div className="flex-1 min-w-0 h-full overflow-hidden relative z-0">
            <InvestigationIntakeScreen
              onLoadGraph={handleStartTrace}
              isLoading={isLoadingGraph}
            />
          </div>
        )}

        {/* Stage 3: Trace connections verification screen (Asks Transaction ID & Device ID) */}
        {workspaceStage === 'trace' && (
          <div className="flex-1 min-w-0 h-full overflow-hidden relative z-0">
            <TraceConnectionsScreen
              complaintId={activeCaseId}
              defaultTransactionId={activeTxnId}
              defaultDeviceId={activeDevId}
              onBackToComplaints={handleReturnToComplaints}
              onOpenInvestigation={handleOpenInvestigation}
            />
          </div>
        )}

        {/* Stage 4: Investigation Workspace (Graph is NOT open automatically, only opens on Analysis) */}
        {workspaceStage === 'investigation' && (
          <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative z-0 animate-in fade-in duration-200">
            {/* 1. WORKSPACE SUB-HEADER STRIP WITH INTERACTIVE SLIDER BUTTON */}
            <div className="h-10 px-4 bg-white border-b border-[#E8E4D8] flex items-center justify-between text-xs text-slate-700 shrink-0 shadow-2xs select-none gap-3">
              {/* Left: Case Info & Status */}
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#007065] animate-pulse" />
                  <span className="font-bold text-xs text-slate-800 tracking-tight">
                    NCRP Investigation Workspace
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-slate-100 text-slate-600 border border-slate-200">
                    {activeCaseId}
                  </span>
                </div>

                <div className="hidden md:flex items-center gap-1.5 text-[11px] text-slate-500 font-medium">
                  <span>•</span>
                  <span>Txn: <code className="font-mono text-slate-700">{activeTxnId}</code></span>
                  <span>•</span>
                  <span>Device: <code className="font-mono text-slate-700">{activeDevId}</code></span>
                </div>
              </div>

              {/* Right: Interactive Slider Button & Analysis Trigger */}
              <div className="flex items-center gap-2.5 shrink-0">
                {/* Interactive Slider Button for Partial Text Side (Toggle Open/Hide) */}
                {isGraphVisible && (
                  <button
                    onClick={() => setIsTextPanelOpen((prev) => !prev)}
                    className={`px-3 py-1 rounded-xl border text-[11px] font-bold flex items-center gap-2 transition-all shadow-2xs cursor-pointer select-none ${
                      isTextPanelOpen
                        ? 'bg-emerald-50 border-emerald-300 text-[#007065]'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                    title={isTextPanelOpen ? 'Click to hide partial text panel' : 'Click to slide open partial text panel'}
                  >
                    <SlidersHorizontal className="w-3.5 h-3.5 text-[#007065]" />
                    <span>Insights Panel</span>
                    {/* Visual Slide Toggle Switch */}
                    <div
                      className={`w-7 h-3.5 rounded-full transition-colors relative flex items-center px-0.5 ${
                        isTextPanelOpen ? 'bg-[#007065]' : 'bg-slate-300'
                      }`}
                    >
                      <div
                        className={`w-2.5 h-2.5 rounded-full bg-white shadow-xs transition-transform duration-200 ${
                          isTextPanelOpen ? 'translate-x-3.5' : 'translate-x-0'
                        }`}
                      />
                    </div>
                  </button>
                )}

                <button
                  onClick={() => {
                    if (!isGraphVisible) {
                      handleRunAnalysis();
                    } else {
                      setIsGraphVisible(false);
                    }
                  }}
                  title={isGraphVisible ? 'Hide Network Graph' : 'Run Analysis (Show Graph)'}
                  className="px-3 py-1 rounded-xl bg-[#007065] hover:bg-[#005a52] text-white text-[11px] font-bold flex items-center gap-1.5 shadow-2xs transition-all cursor-pointer"
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>{isGraphVisible ? 'Graph Active' : 'Analysis (Show Graph)'}</span>
                </button>
              </div>
            </div>

            {/* 2. MAIN WORKSPACE BODY */}
            <div className="flex-1 flex min-h-0 relative overflow-hidden bg-[#FBF9F4]">
              {/* Scenario A: Graph is Hidden (Initial state prior to clicking Analysis) */}
              {!isGraphVisible ? (
                <div className="w-full h-full p-4 overflow-hidden animate-in fade-in duration-200">
                  <div className="h-full rounded-2xl overflow-hidden border border-[#E8E4D8] shadow-2xs bg-white">
                    <InvestigationInsightsRail
                      selectedNode={selectedNetworkNode}
                      onClearSelection={() => setSelectedNetworkNode(null)}
                      edges={networkEdges}
                      nodes={networkNodes}
                      frozenNodeIds={frozenNodeIds}
                      onToggleFreeze={handleToggleFreeze}
                      onDownloadReport={handleDownloadReport}
                      onOpenComplaints={() => handleToggleDrawer('complaints')}
                      complaintCount={complaints.length}
                      onShowGraph={handleRunAnalysis}
                      onRunAnalysis={handleRunAnalysis}
                      isGraphVisible={isGraphVisible}
                      caseId={activeCaseId}
                    />
                  </div>
                </div>
              ) : (
                /* Scenario B: Graph is Visible -> Partial Text Side with Slider Toggle */
                <div className="w-full h-full flex min-h-0 overflow-hidden relative">
                  {/* Partial Text Side Panel (Slides open or collapses based on slider button) */}
                  <div
                    className={`h-full transition-all duration-300 ease-in-out overflow-hidden shrink-0 ${
                      isTextPanelOpen
                        ? 'w-[380px] lg:w-[420px] p-2.5 pr-0 opacity-100'
                        : 'w-0 p-0 opacity-0 pointer-events-none'
                    }`}
                  >
                    <div className="w-[380px] lg:w-[420px] h-full rounded-2xl overflow-hidden border border-[#E8E4D8] shadow-2xs bg-white">
                      <InvestigationInsightsRail
                        selectedNode={selectedNetworkNode}
                        onClearSelection={() => setSelectedNetworkNode(null)}
                        edges={networkEdges}
                        nodes={networkNodes}
                        frozenNodeIds={frozenNodeIds}
                        onToggleFreeze={handleToggleFreeze}
                        onDownloadReport={handleDownloadReport}
                        onOpenComplaints={() => handleToggleDrawer('complaints')}
                        complaintCount={complaints.length}
                        onShowGraph={handleRunAnalysis}
                        onRunAnalysis={handleRunAnalysis}
                        isGraphVisible={isGraphVisible}
                        caseId={activeCaseId}
                      />
                    </div>
                  </div>

                  {/* Interactive Edge Slider Toggle Handle Button */}
                  <div className="flex items-center shrink-0 z-30">
                    <button
                      onClick={() => setIsTextPanelOpen((prev) => !prev)}
                      className="w-5 h-14 -ml-0.5 bg-white hover:bg-slate-50 border border-[#E8E4D8] rounded-r-lg shadow-xs flex items-center justify-center text-slate-500 hover:text-[#007065] transition-all cursor-pointer group"
                      title={isTextPanelOpen ? 'Slide hide text panel' : 'Slide open partial text panel'}
                    >
                      <ChevronLeft
                        className={`w-3.5 h-3.5 transition-transform duration-300 ${
                          isTextPanelOpen ? '' : 'rotate-180'
                        }`}
                      />
                    </button>
                  </div>

                  {/* Interactive Network Graph & Timeline Canvas (Expands dynamically to fill remaining or 100% space) */}
                  <section className="h-full flex-1 min-w-0 flex flex-col p-2.5 overflow-hidden">
                    {/* Main Graph Area: Pure SVG NetworkGraphCanvas */}
                    <div className="flex-1 min-h-0 relative rounded-t-2xl border border-[#E8E4D8] border-b-0 shadow-2xs overflow-hidden bg-white">
                      <NetworkGraphCanvas
                        nodes={networkNodes}
                        edges={networkEdges}
                        selectedNodeId={selectedNetworkNode?.id || null}
                        onSelectNode={setSelectedNetworkNode}
                        timelineIndex={timelineIndex}
                        frozenNodeIds={frozenNodeIds}
                      />
                    </div>

                    {/* Lower: Transaction Timeline Bar (Positioned flush beneath graph) */}
                    <div className="shrink-0 rounded-b-2xl overflow-hidden border border-[#E8E4D8] shadow-2xs">
                      <TransactionTimelineBar
                        timelineIndex={timelineIndex}
                        setTimelineIndex={setTimelineIndex}
                        isPlaying={isPlaying}
                        setIsPlaying={setIsPlaying}
                        steps={activeCaseData.timelineSteps}
                      />
                    </div>
                  </section>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Slide-In Modal Drawer when Complaints or Past Record are clicked from Sidebar */}
        {activeDrawer && (
          <div className="absolute right-0 top-0 bottom-0 w-[420px] max-w-[90vw] bg-white border-l border-[#E2DFD7] shadow-2xl z-40 flex flex-col animate-in slide-in-from-right duration-200">
            {/* Drawer Close Bar */}
            <div className="px-5 py-3.5 border-b border-[#E2DFD7] flex items-center justify-between bg-slate-50">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                {activeDrawer === 'complaints'
                  ? 'Complaints & Dispute Reports'
                  : activeDrawer === 'timeline'
                  ? 'Fraud Timeline Sequence'
                  : 'Investigation Summary & Audit'}
              </span>
              <button
                onClick={() => setActiveDrawer(null)}
                className="p-1 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 min-h-0 overflow-hidden">
              {activeDrawer === 'complaints' && (
                <ComplaintsPanel
                  complaints={complaints}
                  onUpdateComplaintStatus={handleUpdateComplaintStatus}
                  selectedComplaintId={selectedComplaint?.id || null}
                  onSelectComplaint={handleSelectComplaint}
                  onClose={() => setActiveDrawer(null)}
                />
              )}
              {activeDrawer === 'timeline' && (
                <FraudTimelinePanel
                  timeline={timeline}
                  selectedEventId={selectedTimelineEvent?.id || null}
                  onSelectEvent={handleSelectTimelineEvent}
                  onClose={() => setActiveDrawer(null)}
                />
              )}
              {activeDrawer === 'summary' && (
                <InvestigationSummaryPanel
                  nodes={dataSourceMode === 'live' && liveNodes.length > 0 ? liveNodes : nodes}
                  edges={dataSourceMode === 'live' && liveEdges.length > 0 ? liveEdges : edges}
                  complaints={complaints}
                  onClose={() => setActiveDrawer(null)}
                  onDownloadReport={handleDownloadReport}
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Filter & Threshold Sliders Slidebar */}
      <FilterSlidebar
        isOpen={isFilterSlidebarOpen}
        onClose={() => setIsFilterSlidebarOpen(false)}
        minRiskScore={minRiskScore}
        setMinRiskScore={setMinRiskScore}
        minAmount={minAmount}
        setMinAmount={setMinAmount}
        timeRange={timeRange}
        setTimeRange={setTimeRange}
        filterTypes={filterTypes}
        setFilterTypes={setFilterTypes}
        layoutName={layoutName}
        setLayoutName={setLayoutName}
        onReset={resetFilters}
      />

      {/* Complaint Intake Modal */}
      <ComplaintIntakeModal
        isOpen={complaintModalOpen}
        onClose={() => setComplaintModalOpen(false)}
        onAddComplaint={handleAddComplaint}
        existingAccounts={nodes.filter((n) => n.type === 'account')}
      />
    </div>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <DashboardContent />
    </ThemeProvider>
  );
}

export default App;

