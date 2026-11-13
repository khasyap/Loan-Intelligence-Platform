import React from "react";
import { 
  Building2, 
  BarChart3, 
  ShieldAlert, 
  Layers, 
  AlertTriangle, 
  CalendarClock, 
  PlusCircle 
} from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenOriginationModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenOriginationModal,
}) => {
  const navItems = [
    { id: "executive", label: "Executive Suite", icon: BarChart3 },
    { id: "risk", label: "Risk & Compliance", icon: ShieldAlert },
    { id: "operations", label: "Operations Funnel", icon: Layers },
    { id: "anomalies", label: "Anomaly Lab", icon: AlertTriangle },
    { id: "repayments", label: "Amortization Tracker", icon: CalendarClock },
  ];

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-lg text-white shadow-lg shadow-cyan-500/20">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Loan Intelligence Platform
              </span>
              <div className="text-[10px] text-cyan-400 font-mono tracking-wider">
                ORIGINATION & RISK DECISIONING SYSTEM
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Action Button */}
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
              CORE API ONLINE
            </span>
            <button
              onClick={onOpenOriginationModal}
              className="flex items-center space-x-2 px-3.5 py-1.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-lg text-sm font-medium shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Simulate Loan</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

