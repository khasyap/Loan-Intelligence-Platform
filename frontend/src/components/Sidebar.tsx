import React, { useState } from "react";
import { 
  Building2, 
  BarChart3, 
  ShieldAlert, 
  Layers, 
  AlertTriangle, 
  CalendarClock, 
  UserCheck, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  PlusCircle, 
  LogOut, 
  UserCircle2, 
  Shield, 
  Check, 
  Lock
} from "lucide-react";
import { UserProfile, UserRole } from "../types";
import { ThemeToggle } from "./ThemeToggle";

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: UserRole[];
  badge?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
  currentUser: UserProfile;
  onSwitchRole: (role: UserRole) => void;
  onOpenOriginationModal: () => void;
}

const navSections: NavSection[] = [
  {
    title: "PORTFOLIO & RISK",
    items: [
      { id: "executive", label: "Executive Suite", icon: BarChart3, roles: ["ADMIN", "RISK_REVIEWER"] },
      { id: "risk", label: "Risk & Compliance", icon: ShieldAlert, roles: ["ADMIN", "RISK_REVIEWER"], badge: "Fair Lending" },
    ],
  },
  {
    title: "OPERATIONS & QUEUES",
    items: [
      { id: "operations", label: "Operations Funnel", icon: Layers, roles: ["ADMIN", "RISK_REVIEWER", "OPERATIONS_ANALYST"] },
      { id: "repayments", label: "Amortization Tracker", icon: CalendarClock, roles: ["ADMIN", "RISK_REVIEWER", "OPERATIONS_ANALYST", "CUSTOMER"] },
    ],
  },
  {
    title: "AUDIT & QUALITY",
    items: [
      { id: "anomalies", label: "Anomaly Lab", icon: AlertTriangle, roles: ["ADMIN", "RISK_REVIEWER"], badge: "F1=1.0" },
    ],
  },
  {
    title: "BORROWER EXPERIENCE",
    items: [
      { id: "customer_portal", label: "Customer Portal", icon: UserCheck, roles: ["CUSTOMER", "ADMIN"] },
    ],
  },
];

const DEMO_ROLES: { role: UserRole; title: string; email: string; color: string }[] = [
  { role: "ADMIN", title: "System Administrator", email: "admin@bank.org", color: "text-purple-400 bg-purple-500/10 border-purple-500/20" },
  { role: "RISK_REVIEWER", title: "Senior Underwriter", email: "reviewer@bank.org", color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
  { role: "OPERATIONS_ANALYST", title: "Operations Analyst", email: "ops@bank.org", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  { role: "CUSTOMER", title: "Loan Applicant", email: "customer@bank.org", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
  isMobileOpen,
  setIsMobileOpen,
  currentUser,
  onSwitchRole,
  onOpenOriginationModal,
}) => {
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const handleSelectNav = (tabId: string) => {
    setActiveTab(tabId);
    setIsMobileOpen(false);
  };

  const getRoleBadgeStyle = (role: UserRole) => {
    switch (role) {
      case "ADMIN":
        return "bg-purple-500/20 text-purple-600 dark:text-purple-300 border-purple-500/30";
      case "RISK_REVIEWER":
        return "bg-indigo-500/20 text-indigo-600 dark:text-indigo-300 border-indigo-500/30";
      case "OPERATIONS_ANALYST":
        return "bg-amber-500/20 text-amber-600 dark:text-amber-300 border-amber-500/30";
      case "CUSTOMER":
        return "bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 border-emerald-500/30";
    }
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 select-none transition-colors duration-200">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="flex-shrink-0 p-2.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-xl text-white shadow-lg shadow-cyan-500/20">
            <Building2 className="w-5 h-5" />
          </div>
          {!isCollapsed && (
            <div className="min-w-0 flex-1">
              <h1 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight truncate leading-tight">
                Loan Intelligence
              </h1>
              <div className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono tracking-wider font-semibold truncate">
                ORIGINATION &amp; RISK
              </div>
            </div>
          )}
        </div>

        {/* Desktop Collapse Toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="hidden lg:flex items-center justify-center p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>

        {/* Mobile Close Button */}
        <button
          onClick={() => setIsMobileOpen(false)}
          className="lg:hidden p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Quick Action Button */}
      <div className="p-3">
        <button
          onClick={() => {
            onOpenOriginationModal();
            setIsMobileOpen(false);
          }}
          className={`w-full flex items-center justify-center space-x-2 py-2.5 px-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-cyan-500/10 transition-all cursor-pointer ${
            isCollapsed ? "px-0" : ""
          }`}
          title="Simulate Loan"
        >
          <PlusCircle className="w-4 h-4 flex-shrink-0" />
          {!isCollapsed && <span>Simulate Loan</span>}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
        {navSections.map((section) => {
          const visibleItems = section.items.filter((item) =>
            item.roles.includes(currentUser.role)
          );

          if (visibleItems.length === 0) return null;

          return (
            <div key={section.title} className="space-y-1">
              {!isCollapsed && (
                <div className="px-3 pb-1 text-[10px] font-mono font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
                  {section.title}
                </div>
              )}
              {visibleItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectNav(item.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                      isActive
                        ? "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/25 shadow-sm font-semibold"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
                    }`}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? "text-cyan-600 dark:text-cyan-400" : "text-slate-500 dark:text-slate-400"}`} />
                    {!isCollapsed && (
                      <div className="flex-1 flex items-center justify-between min-w-0">
                        <span className="truncate">{item.label}</span>
                        {item.badge && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono border border-slate-200 dark:border-slate-700">
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Theme Toggle & User Profile Section */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/60 dark:bg-slate-950/40 relative space-y-2">
        {/* Theme Switcher */}
        <div className={`flex items-center ${isCollapsed ? "justify-center" : "justify-between px-1"}`}>
          {!isCollapsed && <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Appearance</span>}
          <ThemeToggle compact={isCollapsed} />
        </div>

        {/* Profile Button */}
        <button
          onClick={() => setShowRoleMenu(!showRoleMenu)}
          className={`w-full flex items-center space-x-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors text-left cursor-pointer ${
            isCollapsed ? "justify-center px-0" : ""
          }`}
          title="Switch Demo Role"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xs flex-shrink-0 shadow-sm">
            {currentUser.name.split(" ").map((n) => n[0]).join("")}
          </div>
          {!isCollapsed && (
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-slate-900 dark:text-white truncate flex items-center justify-between">
                <span>{currentUser.name}</span>
              </div>
              <div className="flex items-center space-x-1.5 mt-0.5">
                <span className={`inline-block px-1.5 py-0.2 rounded text-[10px] font-mono border ${getRoleBadgeStyle(currentUser.role)}`}>
                  {currentUser.role}
                </span>
              </div>
            </div>
          )}
        </button>

        {/* Role Switcher Popover */}
        {showRoleMenu && (
          <div className="absolute bottom-20 left-2 right-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-2 shadow-2xl z-50 space-y-1 animate-in fade-in duration-150">
            <div className="px-2 py-1 text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase font-semibold">
              Switch RBAC Role (Live Demo)
            </div>
            {DEMO_ROLES.map((r) => (
              <button
                key={r.role}
                onClick={() => {
                  onSwitchRole(r.role);
                  setShowRoleMenu(false);
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left cursor-pointer ${
                  currentUser.role === r.role
                    ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-medium border border-slate-200 dark:border-slate-700"
                    : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                }`}
              >
                <div>
                  <div className="font-medium">{r.title}</div>
                  <div className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">{r.email}</div>
                </div>
                {currentUser.role === r.role && <Check className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400 flex-shrink-0" />}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed / Collapsible Sidebar */}
      <aside
        className={`hidden lg:block fixed top-0 bottom-0 left-0 z-30 transition-all duration-300 ease-in-out ${
          isCollapsed ? "w-20" : "w-64"
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer (Slide-out) */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 animate-fade-in">
          {/* Backdrop */}
          <div
            onClick={() => setIsMobileOpen(false)}
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm cursor-pointer"
          />

          {/* Sliding Panel */}
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl z-10">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
