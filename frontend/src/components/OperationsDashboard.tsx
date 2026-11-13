import React, { useEffect, useState } from "react";
import { 
  Layers, 
  FileCheck, 
  Clock, 
  Search, 
  Filter, 
  ArrowRight, 
  CheckCircle2, 
  XCircle, 
  ShieldAlert, 
  AlertCircle, 
  X, 
  Eye, 
  Coins 
} from "lucide-react";
import { 
  fetchOperationsAnalytics, 
  fetchApplications, 
  fetchDocuments, 
  verifyDocument, 
  submitDecisionOverride, 
  fetchDisbursementEligibility,
  fetchApplicationDetail 
} from "../services/api";
import { OperationsAnalytics, ApplicationItem, UserProfile } from "../types";
import { ExportMenu } from "./ExportMenu";

interface OperationsDashboardProps {
  onSelectApplication: (applicationId: string) => void;
  currentUser?: UserProfile;
}

export const OperationsDashboard: React.FC<OperationsDashboardProps> = ({
  onSelectApplication,
  currentUser,
}) => {
  const [analytics, setAnalytics] = useState<OperationsAnalytics | null>(null);
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");

  // Modals state
  const [reviewApp, setReviewApp] = useState<ApplicationItem | null>(null);
  const [overrideStatus, setOverrideStatus] = useState<string>("APPROVED");
  const [overrideReason, setOverrideReason] = useState<string>("");
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [overrideMsg, setOverrideMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Disbursement Check Modal
  const [gateAppId, setGateAppId] = useState<string | null>(null);
  const [gateResult, setGateResult] = useState<any | null>(null);
  const [gateLoading, setGateLoading] = useState(false);

  const loadData = () => {
    Promise.all([fetchOperationsAnalytics(), fetchApplications(selectedStatus || undefined)])
      .then(([ops, apps]) => {
        setAnalytics(ops);
        setApplications(apps);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [selectedStatus]);

  const handleOpenReview = (app: ApplicationItem) => {
    setReviewApp(app);
    setOverrideStatus("APPROVED");
    setOverrideReason("Senior underwriter discretionary credit policy exception approved based on low risk profile.");
    setOverrideMsg(null);
  };

  const handleExecuteOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewApp) return;
    setOverrideLoading(true);
    setOverrideMsg(null);
    try {
      const detail = await fetchApplicationDetail(reviewApp.application_id);
      const decId = detail.decision?.decision_id || `DEC-${reviewApp.application_id}-01`;
      await submitDecisionOverride(decId, overrideStatus, overrideReason);
      setOverrideMsg({ type: "success", text: `Decision override successfully recorded as ${overrideStatus}` });
      loadData();
      setTimeout(() => setReviewApp(null), 1200);
    } catch (err: any) {
      setOverrideMsg({ type: "error", text: err.message || "Failed to submit override" });
    } finally {
      setOverrideLoading(false);
    }
  };

  const handleCheckDisbursement = async (appId: string) => {
    setGateAppId(appId);
    setGateLoading(true);
    try {
      const res = await fetchDisbursementEligibility(appId);
      setGateResult(res);
    } catch (err: any) {
      setGateResult({ is_disbursement_eligible: false, reasons: [err.message || "Eligibility check failed"] });
    } finally {
      setGateLoading(false);
    }
  };

  const filteredApps = applications.filter((app) => {
    return (
      app.application_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.applicant_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.product_id.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 dark:text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-cyan-500 mr-3"></div>
        Loading Operations Funnel &amp; Document Queues...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Funnel & Document Verification Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lifecycle Funnel */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Layers className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Application Lifecycle Funnel</h3>
            </div>
            <ExportMenu
              baseEndpoint="/exports/operations"
              defaultFilename="Operations_Funnel_Report"
              label="Export Funnel"
              size="sm"
            />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {analytics?.lifecycle_funnel.map((item) => (
              <div key={item.status} className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/90 rounded-xl p-3">
                <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">{item.status}</div>
                <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-1">{item.count}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Document Verification Queue */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <FileCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Document Verification Health</h3>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {analytics?.document_verification_summary.map((item) => {
              const isVer = item.status === "VERIFIED";
              const isRej = item.status === "REJECTED";
              return (
                <div key={item.status} className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/90 rounded-xl p-3">
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">{item.status}</div>
                  <div
                    className={`text-xl font-bold font-mono mt-1 ${
                      isVer
                        ? "text-emerald-600 dark:text-emerald-400"
                        : isRej
                        ? "text-rose-600 dark:text-rose-400"
                        : "text-amber-600 dark:text-amber-400"
                    }`}
                  >
                    {item.count}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Applications Operations Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Application Processing Queue</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Filter by underwriting status, inspect loan dossiers, or execute overrides</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative flex-1 sm:flex-initial">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search LOAN / APP..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full sm:w-44 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-700 dark:text-slate-300 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="">All Statuses</option>
              <option value="APPROVED">APPROVED</option>
              <option value="DISBURSED">DISBURSED</option>
              <option value="MANUAL_REVIEW">MANUAL_REVIEW</option>
              <option value="REJECT">REJECT</option>
              <option value="PENDING_INFORMATION">PENDING_INFO</option>
            </select>

            {/* Bulk / Filtered Applications Export */}
            <ExportMenu
              baseEndpoint="/exports/applications"
              queryParams={{ status: selectedStatus, search: searchTerm }}
              defaultFilename="Filtered_Applications_Report"
              label="Export Queue"
              size="sm"
            />
          </div>
        </div>

        {/* Responsive Table Container */}
        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300 min-w-[750px]">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 font-mono text-xs uppercase border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Application ID</th>
                <th className="py-3 px-4">Applicant ID</th>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4 text-right">Principal</th>
                <th className="py-3 px-4 text-center">Tenure</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans text-xs sm:text-sm">
              {filteredApps.slice(0, 25).map((app) => {
                const isApp = app.application_status === "APPROVED" || app.application_status === "DISBURSED";
                const isRej = app.application_status === "REJECT";
                return (
                  <tr key={app.application_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-cyan-600 dark:text-cyan-400">{app.application_id}</td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-500 dark:text-slate-400">{app.applicant_id}</td>
                    <td className="py-3 px-4 text-xs font-mono">{app.product_id}</td>
                    <td className="py-3 px-4 font-mono text-right font-medium text-slate-900 dark:text-white">
                      ₹{app.requested_principal.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-xs text-slate-500 dark:text-slate-400">
                      {app.requested_term_months}m
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${
                          isApp
                            ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20"
                            : isRej
                            ? "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-500/20"
                            : "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20"
                        }`}
                      >
                        {app.application_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Download Individual Dossier */}
                        <ExportMenu
                          baseEndpoint={`/exports/loans/${app.application_id}`}
                          defaultFilename={`Loan_Dossier_${app.application_id}`}
                          label="Dossier"
                          size="sm"
                        />

                        {/* Underwriter Override Button */}
                        <button
                          onClick={() => handleOpenReview(app)}
                          className="px-2 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white rounded text-[11px] font-medium border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                          title="Manual Review / Override"
                        >
                          Review
                        </button>

                        {/* Disbursement Gate Check */}
                        <button
                          onClick={() => handleCheckDisbursement(app.application_id)}
                          className="px-2 py-1 bg-cyan-50 dark:bg-cyan-950/60 hover:bg-cyan-100 dark:hover:bg-cyan-900/60 text-cyan-700 dark:text-cyan-300 rounded text-[11px] font-medium border border-cyan-200 dark:border-cyan-800/40 transition-colors cursor-pointer"
                          title="Check Disbursement Gate"
                        >
                          Gate
                        </button>

                        {/* Amortization Schedule */}
                        <button
                          onClick={() => onSelectApplication(app.application_id)}
                          className="inline-flex items-center text-xs text-cyan-600 dark:text-cyan-400 hover:text-cyan-500 font-medium px-1.5 py-1 cursor-pointer"
                          title="Amortization Schedule"
                        >
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Review / Underwriter Override Modal */}
      {reviewApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <button
              onClick={() => setReviewApp(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400 mb-2">
              <ShieldAlert className="w-5 h-5" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider">Human Underwriting Override</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Manual Review Decision</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Recording an authorized underwriter override creates an immutable audit trail in <code className="text-cyan-600 dark:text-cyan-400">decision_override_history</code>.
            </p>

            {overrideMsg && (
              <div className={`mb-4 p-3 rounded-lg text-xs flex items-center space-x-2 ${
                overrideMsg.type === "success" 
                  ? "bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-400"
                  : "bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-700 dark:text-rose-400"
              }`}>
                {overrideMsg.type === "success" ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
                <span>{overrideMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleExecuteOverride} className="space-y-4">
              <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-3 text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Application:</span>
                  <span className="font-mono text-slate-900 dark:text-white font-medium">{reviewApp.application_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Current Status:</span>
                  <span className="font-mono text-amber-600 dark:text-amber-400">{reviewApp.application_status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Principal:</span>
                  <span className="font-mono text-emerald-600 dark:text-emerald-400">₹{reviewApp.requested_principal.toLocaleString()}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Target Decision</label>
                <select
                  value={overrideStatus}
                  onChange={(e) => setOverrideStatus(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 font-mono"
                >
                  <option value="APPROVED">APPROVED (Underwriter Exception)</option>
                  <option value="REJECT">REJECT (Policy Failure)</option>
                  <option value="PENDING_INFORMATION">PENDING_INFORMATION (Require Documentation)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Audit Justification &amp; Policy Reason</label>
                <textarea
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-2.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                  placeholder="Provide explicit credit reason for regulatory audit..."
                  required
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setReviewApp(null)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideLoading}
                  className="flex items-center space-x-1.5 px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-400 hover:to-blue-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all disabled:opacity-50 cursor-pointer"
                >
                  {overrideLoading ? <span>Recording...</span> : <span>Confirm Override</span>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Disbursement Prerequisite Gate Modal */}
      {gateAppId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <button
              onClick={() => { setGateAppId(null); setGateResult(null); }}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-2 text-cyan-600 dark:text-cyan-400 mb-2">
              <Coins className="w-5 h-5" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider">Disbursement Prerequisite Gate</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{gateAppId}</h2>

            {gateLoading ? (
              <div className="py-8 text-center text-slate-500 dark:text-slate-400 text-xs">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-cyan-500 mx-auto mb-2"></div>
                Evaluating strict prerequisite checklist...
              </div>
            ) : gateResult ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-xl border flex items-center space-x-3 ${
                  gateResult.is_disbursement_eligible
                    ? "bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-400"
                    : "bg-rose-50 dark:bg-rose-500/10 border-rose-200 dark:border-rose-500/20 text-rose-700 dark:text-rose-400"
                }`}>
                  {gateResult.is_disbursement_eligible ? (
                    <CheckCircle2 className="w-6 h-6 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-6 h-6 flex-shrink-0" />
                  )}
                  <div>
                    <div className="font-semibold text-sm">
                      {gateResult.is_disbursement_eligible ? "DISBURSEMENT ELIGIBLE" : "PREREQUISITE BLOCKED"}
                    </div>
                    <div className="text-xs opacity-80 mt-0.5">
                      {gateResult.is_disbursement_eligible 
                        ? "All 4 prerequisite gates passed cleanly. Ready for payout."
                        : "Application failed one or more mandatory eligibility requirements."}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase font-mono">Evaluation Breakdown:</div>
                  <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                    {gateResult.reasons?.map((r: string, idx: number) => (
                      <li key={idx} className="flex items-start space-x-2 bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                        <span className="text-cyan-600 dark:text-cyan-400 font-mono font-bold">&bull;</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => { setGateAppId(null); setGateResult(null); }}
                    className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-white rounded-lg text-xs font-medium transition-colors cursor-pointer"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
