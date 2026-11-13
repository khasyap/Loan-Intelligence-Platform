import React, { useState, useEffect } from "react";
import { X, CheckCircle2, AlertTriangle, AlertCircle, Sparkles } from "lucide-react";
import { submitApplication, fetchProducts } from "../services/api";
import { ProductItem } from "../types";

interface ApplicationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ApplicationModal: React.FC<ApplicationModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [applicantId, setApplicantId] = useState("APP-2026-000001");
  const [productId, setProductId] = useState("PROD-001");
  const [principal, setPrincipal] = useState<number>(300000);
  const [term, setTerm] = useState<number>(36);
  const [channel, setChannel] = useState("ONLINE_PORTAL");

  const [submitting, setSubmitting] = useState(false);
  const [decisionResult, setDecisionResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchProducts().then(setProducts).catch(console.error);
      setDecisionResult(null);
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitApplication({
        applicant_id: applicantId,
        product_id: productId,
        requested_principal: Number(principal),
        requested_term_months: Number(term),
        submission_channel: channel,
      });
      setDecisionResult(res);
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  const selectedProduct = products.find((p) => p.product_id === productId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-lg p-5 sm:p-6 shadow-2xl relative max-h-[92vh] overflow-y-auto transition-colors">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2 text-cyan-600 dark:text-cyan-400 mb-2">
          <Sparkles className="w-5 h-5" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider">Live Underwriting Sandbox</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Simulate Loan Origination</h2>

        {error && (
          <div className="mb-4 bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-700 dark:text-rose-400 p-3 rounded-lg text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!decisionResult ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Applicant ID */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Applicant Identifier</label>
              <input
                type="text"
                value={applicantId}
                onChange={(e) => setApplicantId(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500"
                placeholder="APP-2026-000001"
                required
              />
            </div>

            {/* Product Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Loan Product</label>
              <select
                value={productId}
                onChange={(e) => {
                  setProductId(e.target.value);
                  const p = products.find((x) => x.product_id === e.target.value);
                  if (p) {
                    setPrincipal(Number(p.min_principal));
                    setTerm(Number(p.min_term_months));
                  }
                }}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500"
              >
                {products.map((p) => (
                  <option key={p.product_id} value={p.product_id}>
                    {p.product_name} ({p.annual_interest_rate}% p.a.)
                  </option>
                ))}
              </select>
            </div>

            {/* Principal & Term */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Principal (₹)</label>
                <input
                  type="number"
                  value={principal}
                  onChange={(e) => setPrincipal(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500"
                  required
                />
                {selectedProduct && (
                  <div className="text-[10px] text-slate-500 mt-1">
                    Range: ₹{selectedProduct.min_principal.toLocaleString()} - ₹{selectedProduct.max_principal.toLocaleString()}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Tenure (Months)</label>
                <input
                  type="number"
                  value={term}
                  onChange={(e) => setTerm(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500"
                  required
                />
                {selectedProduct && (
                  <div className="text-[10px] text-slate-500 mt-1">
                    Range: {selectedProduct.min_term_months} - {selectedProduct.max_term_months} mos
                  </div>
                )}
              </div>
            </div>

            {/* Channel */}
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Origination Channel</label>
              <select
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="ONLINE_PORTAL">Online Customer Portal</option>
                <option value="MOBILE_APP">Mobile App</option>
                <option value="BRANCH_AGENT">Branch Underwriting Desk</option>
                <option value="PARTNER_API">Fintech Partner API</option>
              </select>
            </div>

            {/* Submit */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold rounded-lg text-sm shadow-md shadow-cyan-500/20 transition-all cursor-pointer disabled:opacity-50"
              >
                {submitting ? "Evaluating Underwriting Rules..." : "Execute Real-Time Underwriting"}
              </button>
            </div>
          </form>
        ) : (
          /* Decision Result Card */
          <div className="space-y-4">
            <div
              className={`p-4 rounded-xl border ${
                decisionResult.decision_status === "APPROVED"
                  ? "bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-400"
                  : decisionResult.decision_status === "REJECT"
                  ? "bg-rose-50 dark:bg-rose-500/10 border-rose-200 dark:border-rose-500/30 text-rose-800 dark:text-rose-400"
                  : "bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/30 text-amber-800 dark:text-amber-400"
              }`}
            >
              <div className="flex items-center space-x-2">
                {decisionResult.decision_status === "APPROVED" ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-rose-600 dark:text-rose-400" />
                )}
                <div>
                  <div className="font-mono text-xs uppercase tracking-wider font-semibold">Underwriting Outcome</div>
                  <div className="text-xl font-bold font-mono">{decisionResult.decision_status}</div>
                </div>
              </div>
              <div className="mt-3 text-xs text-slate-700 dark:text-slate-200">
                <strong>Reason:</strong> {decisionResult.explanation}
              </div>
              <div className="mt-1 text-[11px] font-mono text-slate-500 dark:text-slate-400">
                Code: {decisionResult.reason_code}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 dark:text-slate-400">Proposed EMI</div>
                <div className="font-mono font-bold text-slate-900 dark:text-white mt-1">₹{decisionResult.proposed_monthly_emi.toLocaleString()}</div>
              </div>
              <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 dark:text-slate-400">DTI Ratio</div>
                <div className="font-mono font-bold text-cyan-600 dark:text-cyan-400 mt-1">{decisionResult.dti_ratio}%</div>
              </div>
              <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 dark:text-slate-400">FOIR Ratio</div>
                <div className="font-mono font-bold text-amber-600 dark:text-amber-400 mt-1">{decisionResult.foir_ratio}%</div>
              </div>
            </div>

            <button
              onClick={() => setDecisionResult(null)}
              className="w-full py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-white rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
            >
              Simulate Another Loan
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
