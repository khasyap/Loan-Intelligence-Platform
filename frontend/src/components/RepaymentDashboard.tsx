import React, { useEffect, useState } from "react";
import { 
  CalendarClock, 
  CheckCircle2, 
  AlertCircle, 
  Search, 
  IndianRupee, 
  TrendingDown 
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  Legend 
} from "recharts";
import { fetchRepayments, fetchApplications } from "../services/api";
import { RepaymentDetails } from "../types";
import { ExportMenu } from "./ExportMenu";
import { useTheme } from "../context/ThemeContext";

interface RepaymentDashboardProps {
  selectedAppId?: string;
}

export const RepaymentDashboard: React.FC<RepaymentDashboardProps> = ({
  selectedAppId,
}) => {
  const [appId, setAppId] = useState<string>(selectedAppId || "");
  const [repayment, setRepayment] = useState<RepaymentDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    if (selectedAppId) {
      setAppId(selectedAppId);
      loadSchedule(selectedAppId);
    } else {
      fetchApplications("APPROVED")
        .then((apps) => {
          if (apps.length > 0) {
            setAppId(apps[0].application_id);
            loadSchedule(apps[0].application_id);
          } else {
            fetchApplications("DISBURSED").then((dApps) => {
              if (dApps.length > 0) {
                setAppId(dApps[0].application_id);
                loadSchedule(dApps[0].application_id);
              }
            });
          }
        })
        .catch(console.error);
    }
  }, [selectedAppId]);

  const sampleApprovedLoans = [
    { id: "LOAN-2026-005999", label: "005999 (Approved)", status: "APPROVED" },
    { id: "LOAN-2026-005998", label: "005998 (Approved)", status: "APPROVED" },
    { id: "LOAN-2026-005995", label: "005995 (Disbursed)", status: "DISBURSED" },
    { id: "LOAN-2026-000004", label: "000004 (Disbursed)", status: "DISBURSED" },
  ];

  const loadSchedule = (id: string) => {
    const targetId = id.trim();
    if (!targetId) return;
    setLoading(true);
    setError(null);
    setRepayment(null); // Clear stale repayment data immediately
    fetchRepayments(targetId)
      .then((data) => {
        setRepayment(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load schedule");
        setRepayment(null); // Ensure stale data is never displayed on error
        setLoading(false);
      });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (appId.trim()) {
      loadSchedule(appId.trim());
    }
  };

  const selectSampleLoan = (targetId: string) => {
    setAppId(targetId);
    loadSchedule(targetId);
  };

  const chartData = repayment?.installments.map((inst) => ({
    installment: `M${inst.installment_number}`,
    balance: inst.closing_balance,
    principal: inst.principal_amount,
    interest: inst.interest_amount,
  }));

  const isDark = resolvedTheme === "dark";
  const tooltipBg = isDark ? "#0F172A" : "#FFFFFF";
  const tooltipBorder = isDark ? "#334155" : "#E2E8F0";
  const tooltipText = isDark ? "#F8FAFC" : "#0F172A";
  const gridStroke = isDark ? "#1E293B" : "#F1F5F9";
  const tickColor = isDark ? "#94A3B8" : "#64748B";

  return (
    <div className="space-y-6">
      {/* Header & Application Selector */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-cyan-50 dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-lg border border-cyan-200 dark:border-cyan-500/20">
              <CalendarClock className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Loan Amortization &amp; Repayment Tracker</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                Monthly reducing-balance schedule with automatic penny-rounding reconciliation.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Application */}
            <form onSubmit={handleSearch} className="flex items-center space-x-2 w-full sm:w-auto">
              <input
                type="text"
                placeholder="e.g. LOAN-2026-000004"
                value={appId}
                onChange={(e) => setAppId(e.target.value)}
                className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono flex-1 sm:w-48"
              />
              <button
                type="submit"
                className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-white text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
              >
                Search
              </button>
            </form>

            {/* Export Schedule */}
            {repayment && (
              <ExportMenu
                baseEndpoint={`/exports/repayments/${appId}`}
                defaultFilename={`Repayment_Schedule_${appId}`}
                label="Export Schedule"
              />
            )}
          </div>
        </div>

        {/* Quick Sample Selector */}
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500 dark:text-slate-400 font-medium">Quick Select Facility:</span>
          {sampleApprovedLoans.map((s) => (
            <button
              key={s.id}
              onClick={() => selectSampleLoan(s.id)}
              className={`px-2.5 py-1 rounded-md font-mono text-[11px] transition-colors border cursor-pointer ${
                appId === s.id
                  ? "bg-cyan-50 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border-cyan-300 dark:border-cyan-500/40 font-semibold"
                  : "bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-48 text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-cyan-500 mr-3"></div>
          <span>Retrieving Amortization Schedule for <strong className="font-mono text-cyan-600 dark:text-cyan-400">{appId}</strong>...</span>
        </div>
      )}

      {error && !loading && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
          <div className="bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 rounded-xl p-4 text-rose-700 dark:text-rose-300 text-sm flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-semibold text-rose-800 dark:text-rose-200">Schedule Lookup Notice</div>
              <div className="font-mono text-xs text-rose-600 dark:text-rose-300">{error}</div>
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 rounded-xl p-4 text-xs text-slate-600 dark:text-slate-300 space-y-2">
            <div className="font-semibold text-slate-800 dark:text-white flex items-center space-x-1.5">
              <span>Why am I seeing this?</span>
            </div>
            <p className="leading-relaxed">
              In lending operations and regulatory compliance, reducing-balance repayment schedules are strictly generated for facilities that have passed underwriting and reached <strong className="text-emerald-600 dark:text-emerald-400">APPROVED</strong> or <strong className="text-cyan-600 dark:text-cyan-400">DISBURSED</strong> status.
            </p>
            <p className="leading-relaxed">
              Applications with <strong className="text-rose-600 dark:text-rose-400">REJECT</strong> status (such as <span className="font-mono">{appId}</span>) have zero principal released and no scheduled debtor obligations.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-2">
              <span className="font-medium text-slate-700 dark:text-slate-200">Load an active approved schedule instead:</span>
              <button
                onClick={() => selectSampleLoan("LOAN-2026-005999")}
                className="px-2.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white font-mono rounded text-xs transition-colors cursor-pointer"
              >
                Load LOAN-2026-005999 (Approved)
              </button>
              <button
                onClick={() => selectSampleLoan("LOAN-2026-005998")}
                className="px-2.5 py-1 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-white font-mono rounded text-xs transition-colors cursor-pointer"
              >
                Load LOAN-2026-005998 (Approved)
              </button>
            </div>
          </div>
        </div>
      )}

      {repayment && !loading && (
        <>
          {/* Audit & Reconciliation Summary Card */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
              <div className="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Disbursed Principal</div>
              <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white mt-2">
                ₹{repayment.disbursed_principal.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">{repayment.total_installments} Installments</div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
              <div className="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Total Repaid Principal</div>
              <div className="text-2xl font-bold font-mono text-cyan-600 dark:text-cyan-400 mt-2">
                ₹{repayment.audit_details.total_principal_repaid.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">Variance: ₹{repayment.audit_details.principal_difference}</div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
              <div className="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Total Interest Accrued</div>
              <div className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-2">
                ₹{repayment.audit_details.total_interest.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Installment Sum: ₹{repayment.audit_details.total_installments.toLocaleString()}
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
              <div className="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Reconciliation Audit</div>
              <div className="mt-2 flex items-center space-x-2">
                {repayment.is_reconciled ? (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                    100% RECONCILED
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20">
                    <AlertCircle className="w-3.5 h-3.5 mr-1" />
                    UNRECONCILED
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">Final Balance: ₹0.00</div>
            </div>
          </div>

          {/* Amortization Curve Chart */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Principal Paydown &amp; Balance Amortization</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                  <XAxis dataKey="installment" stroke="#64748b" tick={{ fill: tickColor, fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fill: tickColor, fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, borderRadius: "8px", color: tooltipText }}
                    itemStyle={{ color: tooltipText, fontWeight: 600 }}
                    labelStyle={{ color: tooltipText, fontWeight: 700 }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="balance" name="Remaining Balance" stroke="#06b6d4" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="principal" name="Principal Payment" stroke="#10b981" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="interest" name="Interest Payment" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Installment Schedule Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Installment Schedule Detail</h3>
            <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 max-h-96">
              <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300 min-w-[700px]">
                <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 font-mono text-xs uppercase border-b border-slate-200 dark:border-slate-800 sticky top-0">
                  <tr>
                    <th className="py-3 px-4">#</th>
                    <th className="py-3 px-4">Due Date</th>
                    <th className="py-3 px-4 text-right">Opening Balance</th>
                    <th className="py-3 px-4 text-right">Principal</th>
                    <th className="py-3 px-4 text-right">Interest</th>
                    <th className="py-3 px-4 text-right">EMI</th>
                    <th className="py-3 px-4 text-right">Closing Balance</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-xs">
                  {repayment.installments.map((inst) => (
                    <tr key={inst.schedule_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 px-4 font-bold text-slate-900 dark:text-white">{inst.installment_number}</td>
                      <td className="py-2.5 px-4 text-slate-500 dark:text-slate-400">{inst.due_date}</td>
                      <td className="py-2.5 px-4 text-right">₹{inst.opening_balance.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-right text-emerald-600 dark:text-emerald-400">₹{inst.principal_amount.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-right text-amber-600 dark:text-amber-400">₹{inst.interest_amount.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-right font-bold text-slate-900 dark:text-white">₹{inst.installment_amount.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-right text-cyan-600 dark:text-cyan-400">₹{inst.closing_balance.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-center">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                          {inst.payment_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
