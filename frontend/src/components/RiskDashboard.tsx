import React, { useEffect, useState } from "react";
import { 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  Activity 
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid 
} from "recharts";
import { fetchRiskAnalytics } from "../services/api";
import { RiskAnalytics } from "../types";
import { ExportMenu } from "./ExportMenu";
import { useTheme } from "../context/ThemeContext";

export const RiskDashboard: React.FC = () => {
  const [data, setData] = useState<RiskAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    fetchRiskAnalytics()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 dark:text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-cyan-500 mr-3"></div>
        Loading Risk &amp; Compliance Analytics...
      </div>
    );
  }

  if (!data) {
    return <div className="text-rose-500 p-6">Failed to load risk analytics.</div>;
  }

  const isDark = resolvedTheme === "dark";
  const tooltipBg = isDark ? "#0F172A" : "#FFFFFF";
  const tooltipBorder = isDark ? "#334155" : "#E2E8F0";
  const tooltipText = isDark ? "#F8FAFC" : "#0F172A";
  const gridStroke = isDark ? "#1E293B" : "#F1F5F9";
  const tickColor = isDark ? "#94A3B8" : "#64748B";

  return (
    <div className="space-y-6">
      {/* Fair Lending & Compliance Banner */}
      <div className="bg-white dark:bg-slate-900 border border-indigo-200 dark:border-indigo-500/30 rounded-2xl p-5 sm:p-6 shadow-sm transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 rounded-xl flex-shrink-0">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Fair Lending &amp; Regulatory Compliance Engine</h2>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                Strict adherence to non-discriminatory lending: <strong>Zero protected demographic attributes</strong> (gender, race, ethnicity, religion) are utilized in scoring or decisions.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 self-start sm:self-center">
            <span className="inline-flex items-center px-3 py-1 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 text-xs font-mono font-medium rounded-full border border-indigo-200 dark:border-indigo-500/20 whitespace-nowrap">
              AUDITED: DETERMINISTIC v1.0.0
            </span>
            <ExportMenu
              baseEndpoint="/exports/risk"
              defaultFilename="Risk_Compliance_Report"
              label="Export Risk Report"
            />
          </div>
        </div>
      </div>

      {/* Credit & Affordability Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Credit Score Distribution */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Credit Score Distribution</h3>
            <span className="text-[11px] text-cyan-600 dark:text-cyan-400 font-mono">μ=710, σ=75</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.credit_score_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="range" stroke="#64748b" tick={{ fill: tickColor, fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" tick={{ fill: tickColor, fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, borderRadius: "8px" }}
                  itemStyle={{ color: tooltipText, fontWeight: 600 }}
                  labelStyle={{ color: tooltipText, fontWeight: 700 }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* DTI Ratio Distribution */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Debt-to-Income (DTI)</h3>
            <span className="text-[11px] text-amber-600 dark:text-amber-400 font-mono">Limit: 40-55%</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.dti_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="range" stroke="#64748b" tick={{ fill: tickColor, fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" tick={{ fill: tickColor, fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, borderRadius: "8px" }}
                  itemStyle={{ color: tooltipText, fontWeight: 600 }}
                  labelStyle={{ color: tooltipText, fontWeight: 700 }}
                />
                <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* FOIR Ratio Distribution */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Fixed Obligation (FOIR)</h3>
            <span className="text-[11px] text-rose-600 dark:text-rose-400 font-mono">Limit: 50-65%</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.foir_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="range" stroke="#64748b" tick={{ fill: tickColor, fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748b" tick={{ fill: tickColor, fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, borderColor: tooltipBorder, borderRadius: "8px" }}
                  itemStyle={{ color: tooltipText, fontWeight: 600 }}
                  labelStyle={{ color: tooltipText, fontWeight: 700 }}
                />
                <Bar dataKey="count" fill="#ec4899" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Decision Reason Codes Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm transition-colors">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Underwriting Decision Reason Codes</h3>
        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300 min-w-[550px]">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 font-mono text-xs uppercase border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Reason Code</th>
                <th className="py-3 px-4">Classification</th>
                <th className="py-3 px-4 text-right">Application Count</th>
                <th className="py-3 px-4">Engine Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
              {data.reason_code_distribution.map((r) => {
                const isClean = r.code.startsWith("APP_");
                const isRej = r.code.startsWith("REJ_");
                return (
                  <tr key={r.code} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900 dark:text-white">{r.code}</td>
                    <td className="py-3 px-4 text-xs">
                      {isClean ? "Policy Pass" : isRej ? "Hard Rule Breach" : "Soft Exception / Discretionary"}
                    </td>
                    <td className="py-3 px-4 font-mono text-right font-bold text-slate-900 dark:text-white">{r.count}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono ${
                          isClean
                            ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20"
                            : isRej
                            ? "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20"
                            : "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20"
                        }`}
                      >
                        {isClean ? "APPROVED" : isRej ? "REJECT" : "MANUAL_REVIEW"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
