import React from 'react';
import { 
  ChevronRight, 
  Search, 
  Network,
  Download,
  Plus
} from 'lucide-react';

interface HeaderProps {
  currentInvestigationId?: string;
  onOpenSearch: () => void;
  onOpenAlerts: () => void;
  alertCount?: number;
  onDownloadReport?: () => void;
  onReturnToIntake?: () => void;
  isGraphLoaded?: boolean;
  onLogout?: () => void;
  isLiveConnected?: boolean;
  dataSourceMode?: 'live' | 'mock';
  onSelectDemoScenario?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentInvestigationId = 'INV-2026-084',
  onOpenSearch,
  onOpenAlerts,
  alertCount = 3,
  onDownloadReport,
  onReturnToIntake,
  isGraphLoaded = false,
  onLogout,
  isLiveConnected = false,
  dataSourceMode = 'live',
  onSelectDemoScenario,
}) => {
  return (
    <div className="w-full flex flex-col select-none z-20 shrink-0">
      {/* High-Contrast Top Bar Section */}
      <div className="bg-slate-900 text-slate-100 border-b border-slate-800 px-4 sm:px-6 py-1.5 flex flex-wrap items-center justify-between gap-2.5 text-xs">
        {/* Left: Synthetic Data Notice */}
        <div className="flex items-center gap-2 min-w-0">
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold font-mono tracking-wider uppercase bg-amber-400/20 text-amber-300 border border-amber-400/30 shrink-0">
            NOTICE
          </span>
          <span className="font-semibold text-slate-200 tracking-tight text-[11px] truncate">
            SYNTHETIC DATASET • Investigative Decision Support Prototype{' '}
            <span className="text-slate-400 font-normal hidden lg:inline">
              (Leads for verification, not proof of guilt)
            </span>
          </span>
        </div>

        {/* Center / Right: Demo Scenario Quick-Pill & Live Backend Indicator */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Demo Scenario Quick-Pill */}
          <button
            type="button"
            onClick={onSelectDemoScenario}
            title="Focus on verified demo case: Complaint CMP0004 / Txn TXN002804 / Victim ACC0125 → Beneficiary ACC0135"
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/80 hover:bg-emerald-900 active:scale-[0.98] text-emerald-200 border border-emerald-500/40 text-[11px] font-medium transition-all cursor-pointer shadow-xs group"
          >
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-semibold text-emerald-100 group-hover:text-white transition-colors">Demo Focus:</span>
            <span className="truncate max-w-[280px] sm:max-w-none text-emerald-200/90">
              Complaint CMP0004 / Txn TXN002804 / Victim ACC0125 → Beneficiary ACC0135 (Rapid Onward Transfer)
            </span>
          </button>

          {/* Live Backend Indicator Badge */}
          {isLiveConnected && dataSourceMode === 'live' ? (
            <div
              className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 font-bold text-[11px] tracking-tight shadow-2xs"
              title="Connected to live FastAPI & NetworkX backend API"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] shrink-0" />
              <span>● Live Backend</span>
            </div>
          ) : (
            <div
              className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-950/80 border border-amber-500/50 text-amber-300 font-bold text-[11px] tracking-tight shadow-2xs"
              title="Running in local synthetic demo mode"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
              <span>Offline Demo</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Investigation Header */}
      <header className="h-14 px-5 flex items-center justify-between border-b border-slate-200/90 bg-white shadow-2xs select-none">
      {/* Left: Brand Logo + Breadcrumbs */}
      <div className="flex items-center gap-4">
        {/* Brand Icon & Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#0A7347] flex items-center justify-center text-white shadow-xs">
            <Network className="w-4 h-4 stroke-[2.4]" />
          </div>
          <div className="flex items-baseline">
            <span className="text-base font-bold tracking-tight text-slate-900">
              anvik
            </span>
            <span className="text-[#10B981] font-bold text-lg leading-none ml-0.5">•</span>
          </div>
        </div>

        {/* Vertical Divider */}
        <div className="w-px h-5 bg-slate-200 mx-1" />

        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-xs">
          <span 
            onClick={onReturnToIntake}
            className="text-slate-400 font-medium hover:text-[#007065] cursor-pointer transition-colors"
            title="Return to Complaints & records"
          >
            Workspace
          </span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span 
            onClick={onReturnToIntake}
            className={`font-medium transition-colors cursor-pointer ${
              isGraphLoaded ? 'text-slate-400 hover:text-[#007065]' : 'font-semibold text-slate-900'
            }`}
            title="Return to Complaints & records"
          >
            Complaints & records
          </span>
          {isGraphLoaded && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-mono font-semibold text-xs text-slate-900">
                {currentInvestigationId}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Right: Actions, Search, Avatar */}
      <div className="flex items-center gap-3">
        {/* New Case / Intake Button */}
        {isGraphLoaded && onReturnToIntake && (
          <button
            onClick={onReturnToIntake}
            title="Enter new Transaction ID & Device ID"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 transition-all shadow-2xs btn-press"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Case</span>
          </button>
        )}

        {/* Download Report Button (Only appears after choosing an investigation) */}
        {isGraphLoaded && onDownloadReport && (
          <button
            onClick={onDownloadReport}
            title="Download Forensic Investigation Report (HTML + PDF with Graph Analysis)"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#0D6B42] hover:bg-[#0A5634] text-white transition-all shadow-xs btn-press"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Download Report</span>
          </button>
        )}

        {/* Search Icon */}
        <button
          onClick={onOpenSearch}
          title="Search entities (Ctrl+K)"
          className="p-1.5 rounded-lg transition-colors btn-press text-slate-500 hover:text-slate-900 hover:bg-slate-100"
        >
          <Search className="w-4 h-4" />
        </button>

        {/* Avatar BK with Logout Action */}
        <button
          onClick={onLogout}
          title="Analyst: Bharath K (Click to Log Out)"
          className="w-8 h-8 rounded-full bg-[#0D6B42] hover:bg-[#09472B] active:scale-95 text-white flex items-center justify-center font-bold text-xs ring-1 ring-emerald-500/40 select-none shadow-xs transition-all cursor-pointer"
        >
          BK
        </button>
      </div>
    </header>
  </div>
);
};
