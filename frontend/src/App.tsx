import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { MobileHeader } from "./components/MobileHeader";
import { ExecutiveDashboard } from "./components/ExecutiveDashboard";
import { RiskDashboard } from "./components/RiskDashboard";
import { OperationsDashboard } from "./components/OperationsDashboard";
import { AnomalyDashboard } from "./components/AnomalyDashboard";
import { RepaymentDashboard } from "./components/RepaymentDashboard";
import { CustomerPortal } from "./components/CustomerPortal";
import { ApplicationModal } from "./components/ApplicationModal";
import { loginUser } from "./services/api";
import { UserProfile, UserRole } from "./types";
import { ShieldAlert, ArrowRight, Lock } from "lucide-react";

const DEMO_CREDENTIALS: Record<UserRole, { email: string; pass: string }> = {
  ADMIN: { email: "admin@bank.org", pass: "AdminDemo@2026" },
  RISK_REVIEWER: { email: "reviewer@bank.org", pass: "ReviewerDemo@2026" },
  OPERATIONS_ANALYST: { email: "ops@bank.org", pass: "OpsDemo@2026" },
  CUSTOMER: { email: "customer@bank.org", pass: "CustomerDemo@2026" },
};

const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  ADMIN: ["executive", "risk", "operations", "anomalies", "repayments", "customer_portal"],
  RISK_REVIEWER: ["executive", "risk", "operations", "anomalies", "repayments"],
  OPERATIONS_ANALYST: ["operations", "repayments"],
  CUSTOMER: ["customer_portal", "repayments"],
};

const DEFAULT_TAB_FOR_ROLE: Record<UserRole, string> = {
  ADMIN: "executive",
  RISK_REVIEWER: "risk",
  OPERATIONS_ANALYST: "operations",
  CUSTOMER: "customer_portal",
};

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserProfile>({
    email: "admin@bank.org",
    name: "System Administrator",
    role: "ADMIN",
    access_token: "",
  });

  const [activeTab, setActiveTab] = useState<string>("executive");
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedAppId, setSelectedAppId] = useState<string>("");

  // Authenticate default role on mount
  useEffect(() => {
    loginUser("admin@bank.org", "AdminDemo@2026")
      .then(setCurrentUser)
      .catch(console.error);
  }, []);

  const handleSwitchRole = async (targetRole: UserRole) => {
    try {
      const creds = DEMO_CREDENTIALS[targetRole];
      const profile = await loginUser(creds.email, creds.pass);
      setCurrentUser(profile);
      
      // Auto-switch to an authorized tab for that role
      const allowed = ROLE_PERMISSIONS[targetRole];
      if (!allowed.includes(activeTab)) {
        setActiveTab(DEFAULT_TAB_FOR_ROLE[targetRole]);
      }
    } catch (err) {
      console.error("Role switch failed", err);
    }
  };

  const handleSelectApplication = (id: string) => {
    setSelectedAppId(id);
    setActiveTab("repayments");
  };

  const isTabAllowed = ROLE_PERMISSIONS[currentUser.role].includes(activeTab);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col antialiased text-slate-900 dark:text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-500 transition-colors duration-200">
      {/* Mobile Top Header (< lg) */}
      <MobileHeader
        onOpenMobileMenu={() => setIsMobileOpen(true)}
        onOpenOriginationModal={() => setIsModalOpen(true)}
        currentUser={currentUser}
      />

      <div className="flex-1 flex w-full">
        {/* Responsive Side Navigation */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isCollapsed={isCollapsed}
          setIsCollapsed={setIsCollapsed}
          isMobileOpen={isMobileOpen}
          setIsMobileOpen={setIsMobileOpen}
          currentUser={currentUser}
          onSwitchRole={handleSwitchRole}
          onOpenOriginationModal={() => setIsModalOpen(true)}
        />

        {/* Main Content Area */}
        <div
          className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out ${
            isCollapsed ? "lg:pl-20" : "lg:pl-64"
          }`}
        >
          <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 min-w-0">
            {!isTabAllowed ? (
              /* Access Restricted View */
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 text-center max-w-lg mx-auto my-12 shadow-xl">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-500 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
                  <Lock className="w-6 h-6" />
                </div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Access Restricted (HTTP 403)</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
                  The requested tab <code className="text-cyan-600 dark:text-cyan-400 font-mono font-medium">/{activeTab}</code> is not permitted for your current role (<span className="text-amber-600 dark:text-amber-400 font-mono font-semibold">{currentUser.role}</span>).
                </p>
                <div className="flex justify-center space-x-3">
                  <button
                    onClick={() => setActiveTab(DEFAULT_TAB_FOR_ROLE[currentUser.role])}
                    className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-md transition-all cursor-pointer"
                  >
                    <span>Go to My Dashboard</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <>
                {activeTab === "executive" && <ExecutiveDashboard />}
                {activeTab === "risk" && <RiskDashboard />}
                {activeTab === "operations" && (
                  <OperationsDashboard 
                    onSelectApplication={handleSelectApplication} 
                    currentUser={currentUser}
                  />
                )}
                {activeTab === "anomalies" && <AnomalyDashboard />}
                {activeTab === "repayments" && (
                  <RepaymentDashboard selectedAppId={selectedAppId} />
                )}
                {activeTab === "customer_portal" && (
                  <CustomerPortal
                    currentUser={currentUser}
                    onSelectApplication={handleSelectApplication}
                    onOpenOriginationModal={() => setIsModalOpen(true)}
                  />
                )}
              </>
            )}
          </main>

          {/* Unified Footer */}
          <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-950 py-4 px-4 text-center text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 font-mono transition-colors">
            <div className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-4">
              <span>Loan Intelligence Platform</span>
              <span className="hidden sm:inline text-slate-300 dark:text-slate-700">&bull;</span>
              <span>Deterministic Decisions &amp; Real-Time Risk</span>
              <span className="hidden sm:inline text-slate-300 dark:text-slate-700">&bull;</span>
              <span className="text-cyan-600 dark:text-cyan-400">Synthetic Seed 20261022</span>
            </div>
          </footer>
        </div>
      </div>

      {/* Live Loan Origination Sandbox Modal */}
      <ApplicationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => {}}
      />
    </div>
  );
};

export default App;
