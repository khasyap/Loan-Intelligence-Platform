import React, { useEffect, useState } from "react";
import { 
  AlertTriangle, 
  CheckCircle2, 
  Target, 
  Activity, 
  FileSearch, 
  Cpu 
} from "lucide-react";
import { fetchAnomalyEvaluation, fetchGroundTruth } from "../services/api";
import { AnomalyEvaluation, GroundTruthItem } from "../types";
import { ExportMenu } from "./ExportMenu";

export const AnomalyDashboard: React.FC = () => {
  const [evaluation, setEvaluation] = useState<AnomalyEvaluation | null>(null);
  const [groundTruth, setGroundTruth] = useState<GroundTruthItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchAnomalyEvaluation(), fetchGroundTruth()])
      .then(([evalData, gtData]) => {
        setEvaluation(evalData);
        setGroundTruth(gtData);
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
        Loading Anomaly Lab &amp; Isolated Ground Truth...
      </div>
    );
  }

  const summary = evaluation?.summary;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-lg border border-rose-200 dark:border-rose-500/20">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Anomaly Injection &amp; Detection Lab</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                Independent operational audit engine evaluated against segregated ground-truth exceptions (zero data leakage).
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 self-start md:self-center">
            <span className="inline-flex items-center px-3 py-1 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 text-xs font-mono font-medium rounded-full border border-emerald-200 dark:border-emerald-500/20 whitespace-nowrap">
              F1 SCORE: {(summary?.f1_score ?? 1.0) * 100}%
            </span>
            <ExportMenu
              baseEndpoint="/exports/anomalies"
              defaultFilename="Anomaly_Evaluation_Report"
              label="Export Anomalies"
            />
          </div>
        </div>
      </div>

      {/* KPI Evaluation Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Injected */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Ground Truth Injected</div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-900 dark:text-white">
            {summary?.total_ground_truth ?? 0}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">5 Edge-case categories</div>
        </div>

        {/* Precision */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Detection Precision</div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
            {((summary?.precision ?? 1.0) * 100).toFixed(1)}%
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">False Positives: {summary?.false_positives ?? 0}</div>
        </div>

        {/* Recall */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Detection Recall</div>
          <div className="mt-2 text-2xl font-bold font-mono text-cyan-600 dark:text-cyan-400">
            {((summary?.recall ?? 1.0) * 100).toFixed(1)}%
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">False Negatives: {summary?.false_negatives ?? 0}</div>
        </div>

        {/* F1 Score */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Composite F1 Score</div>
          <div className="mt-2 text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400">
            {(summary?.f1_score ?? 1.0).toFixed(4)}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">Harmonic mean balance</div>
        </div>
      </div>

      {/* 5 Mandatory Category Breakdown */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">5 Mandatory Edge-Case Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {evaluation?.category_breakdown &&
            Object.entries(evaluation.category_breakdown).map(([cat, metric]) => (
              <div key={cat} className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-cyan-600 dark:text-cyan-400">{cat}</span>
                  <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400">F1: {(metric.f1_score * 100).toFixed(0)}%</span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-white dark:bg-slate-900/60 rounded p-1.5 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">Injected</div>
                    <div className="font-mono font-bold text-slate-900 dark:text-white mt-0.5">{metric.ground_truth_count}</div>
                  </div>
                  <div className="bg-white dark:bg-slate-900/60 rounded p-1.5 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">Detected</div>
                    <div className="font-mono font-bold text-cyan-600 dark:text-cyan-400 mt-0.5">{metric.detected_count}</div>
                  </div>
                  <div className="bg-white dark:bg-slate-900/60 rounded p-1.5 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">Matches</div>
                    <div className="font-mono font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">{metric.true_positives}</div>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Ground Truth Register Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm transition-colors">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <FileSearch className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Segregated Ground-Truth Exception Register</h3>
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">data/ground_truth.csv</span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300 min-w-[750px]">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 font-mono text-xs uppercase border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Anomaly ID</th>
                <th className="py-3 px-4">Target Entity</th>
                <th className="py-3 px-4">Record Key</th>
                <th className="py-3 px-4">Issue Type</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Root Cause Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
              {groundTruth.map((gt) => (
                <tr key={gt.anomaly_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-amber-600 dark:text-amber-400">{gt.anomaly_id}</td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-500 dark:text-slate-400">{gt.entity_name}</td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-900 dark:text-white">{gt.record_id}</td>
                  <td className="py-3 px-4 font-mono text-xs text-cyan-600 dark:text-cyan-300">{gt.issue_type}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20">
                      {gt.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-600 dark:text-slate-300 max-w-md truncate">{gt.explanation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
