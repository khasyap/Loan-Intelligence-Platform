import React, { useEffect, useState } from "react";
import {
  Users,
  FileCheck2,
  XCircle,
  Clock,
  IndianRupee,
  Percent,
  ArrowUpRight
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { fetchExecutiveKPIs } from "../services/api";
import { ExecutiveKPIs } from "../types";
import { ExportMenu } from "./ExportMenu";
import { useTheme } from "../context/ThemeContext";

export const ExecutiveDashboard: React.FC = () => {
  const [kpis, setKpis] = useState<ExecutiveKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    fetchExecutiveKPIs()
      .then((data) => {
        setKpis(data);
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
        Loading Executive Portfolio KPIs...
      </div>
    );
  }

  if (!kpis) {
    return <div className="text-rose-500 p-6">Failed to load executive KPIs.</div>;
  }

  const decisionData = [
    { name: "Approved", value: kpis.approved_count, color: "#10b981" },
    { name: "Rejected", value: kpis.rejected_count, color: "#ef4444" },
    { name: "Manual Review", value: kpis.manual_review_count, color: "#f59e0b" },
    { name: "Pending Info", value: kpis.pending_info_count, color: "#06b6d4" },
  ];

  const financialVolumeData = [
    { name: "Requested", amount: kpis.total_requested_principal / 100000 },
    { name: "Approved", amount: kpis.total_approved_principal / 100000 },
    { name: "Disbursed", amount: kpis.total_disbursed_principal / 100000 },
  ];

  // High-contrast, theme-adaptive label renderer
  const renderCustomizedPieLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    name,
    value,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = outerRadius + 22;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    const isRight = x > cx;
    const isDark = resolvedTheme === "dark";

    return (
      <text
        x={x}
        y={y}
        textAnchor={isRight ? "start" : "end"}
        dominantBaseline="central"
        fill={isDark ? "#F8FAFC" : "#0F172A"}
        fontSize="11"
        fontWeight="700"
      >
        {`${name}: ${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  const isDark = resolvedTheme === "dark";
  const tooltipBg = isDark ? "#0F172A" : "#FFFFFF";
  const tooltipBorder = isDark ? "#334155" : "#E2E8F0";
  const tooltipText = isDark ? "#F8FAFC" : "#0F172A";

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">Executive Lending Portfolio</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Deterministic origination volume, risk appetite benchmarks, and liquidity disbursement summary.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <div className="text-xs text-slate-500 dark:text-slate-400">Portfolio Approval Rate</div>
              <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                {kpis.approval_rate}%
              </div>
            </div>
            <div className="border-l border-slate-200 dark:border-slate-800 pl-4">
              <div className="text-xs text-slate-500 dark:text-slate-400">Rejection Rate</div>
              <div className="text-2xl font-bold text-rose-600 dark:text-rose-400 font-mono">
                {kpis.rejection_rate}%
              </div>
            </div>
            {kpis.dataset_profile && (
              <div className="border-l border-slate-200 dark:border-slate-800 pl-4 hidden md:block">
                <div className="text-xs text-slate-500 dark:text-slate-400">Active Profile</div>
                <div className="text-xs font-semibold px-2 py-1 mt-0.5 rounded bg-cyan-50 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
                  {kpis.dataset_profile}
                </div>
              </div>
            )}
            <div className="border-l border-slate-200 dark:border-slate-800 pl-4">
              <ExportMenu
                baseEndpoint="/exports/executive"
                defaultFilename="Executive_Portfolio_Report"
                label="Export Portfolio"
              />
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Applicants */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Applicants</span>
            <Users className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white font-mono">
            {kpis.total_applicants.toLocaleString()}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400 flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-500 mr-1" />
            <span>Master Borrowers Synthesized</span>
          </div>
        </div>

        {/* Total Applications */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Loan Applications</span>
            <FileCheck2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white font-mono">
            {kpis.total_applications.toLocaleString()}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400 flex items-center">
            <span>Approved: {kpis.approved_count} ({kpis.approval_rate}%)</span>
          </div>
        </div>

        {/* Manual Review Required */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Manual Review</span>
            <Clock className="w-5 h-5 text-amber-500 dark:text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono">
            {kpis.manual_review_count.toLocaleString()}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Borderline score &amp; tenure review
          </div>
        </div>

        {/* Total Disbursed */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Disbursed</span>
            <IndianRupee className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono truncate">
            ₹{(kpis.total_disbursed_principal / 10000000).toFixed(2)} Cr
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Verified prerequisite releases
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Decision Breakdown Chart */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Underwriting Decision Distribution</h2>
          <div className="h-72 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 10, right: 30, left: 30, bottom: 10 }}>
                <Pie
                  data={decisionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={78}
                  paddingAngle={4}
                  dataKey="value"
                  label={renderCustomizedPieLabel}
                  labelLine={{ stroke: isDark ? "#64748B" : "#94A3B8", strokeWidth: 1.5 }}
                >
                  {decisionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: "8px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)",
                    color: tooltipText,
                  }}
                  itemStyle={{ color: tooltipText, fontWeight: 600 }}
                  labelStyle={{ color: tooltipText, fontWeight: 700 }}
                  formatter={(val: any) => [`${Number(val).toLocaleString()} Applications`, "Volume"]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
            {decisionData.map((d) => (
              <div key={d.name} className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }}></span>
                <span className="truncate">{d.name}: <strong className="text-slate-900 dark:text-white font-mono">{d.value}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Financial Volume Bar Chart */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Capital Pipeline (₹ in Lakhs)</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={financialVolumeData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748b" tick={{ fill: isDark ? "#94a3b8" : "#475569", fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fill: isDark ? "#94a3b8" : "#475569", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: "8px",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)",
                    color: tooltipText,
                  }}
                  itemStyle={{ color: tooltipText, fontWeight: 600 }}
                  labelStyle={{ color: tooltipText, fontWeight: 700 }}
                  formatter={(val: any) => [`₹${Number(val).toLocaleString()} Lakhs`, "Amount"]}
                />
                <Bar dataKey="amount" fill="#0284c7" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap gap-2 justify-between text-[11px] sm:text-xs text-slate-500 dark:text-slate-400">
            <span>Requested: ₹{(kpis.total_requested_principal / 10000000).toFixed(2)} Cr</span>
            <span>Approved: ₹{(kpis.total_approved_principal / 10000000).toFixed(2)} Cr</span>
            <span>Disbursed: ₹{(kpis.total_disbursed_principal / 10000000).toFixed(2)} Cr</span>
          </div>
        </div>
      </div>
    </div>
  );
};
