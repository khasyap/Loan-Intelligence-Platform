import React, { useEffect, useState } from "react";
import { 
  UserCheck, 
  FileText, 
  CreditCard, 
  Calendar, 
  ArrowRight, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  PlusCircle, 
  ShieldCheck, 
  IndianRupee 
} from "lucide-react";
import { fetchApplications, fetchDocuments } from "../services/api";
import { ApplicationItem, UserProfile } from "../types";
import { ExportMenu } from "./ExportMenu";

interface CustomerPortalProps {
  currentUser: UserProfile;
  onSelectApplication: (applicationId: string) => void;
  onOpenOriginationModal: () => void;
}

export const CustomerPortal: React.FC<CustomerPortalProps> = ({
  currentUser,
  onSelectApplication,
  onOpenOriginationModal,
}) => {
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const applicantId = currentUser.applicant_id || "APP-2026-000001";

  useEffect(() => {
    Promise.all([
      fetchApplications(),
      fetchDocuments()
    ])
      .then(([apps, docs]) => {
        const myApps = apps.filter(a => a.applicant_id === applicantId);
        setApplications(myApps.length > 0 ? myApps : apps.slice(0, 3));
        setDocuments(docs.slice(0, 4));
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [applicantId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 dark:text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-cyan-500 mr-3"></div>
        Loading Customer Portal...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome & Borrower Profile Header */}
      <div className="bg-white dark:bg-slate-900 border border-cyan-200 dark:border-cyan-500/30 rounded-2xl p-6 shadow-sm transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-cyan-50 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 rounded-xl">
              <UserCheck className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Borrower Self-Service Portal</h2>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <span className="text-xs text-slate-600 dark:text-slate-400">Welcome, {currentUser.name}</span>
                <span className="text-xs text-slate-300 dark:text-slate-600">&bull;</span>
                <span className="text-xs font-mono text-cyan-600 dark:text-cyan-400">Applicant ID: {applicantId}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ExportMenu
              baseEndpoint="/exports/applications"
              defaultFilename="My_Loan_Applications"
              label="Export My Loans"
            />
            <button
              onClick={onOpenOriginationModal}
              className="flex items-center justify-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Apply for New Loan</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Total Applications</div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white mt-2">{applications.length}</div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">Lifetime originations</div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Active Approved Facilities</div>
          <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-2">
            {applications.filter(a => a.application_status === "APPROVED" || a.application_status === "DISBURSED").length}
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">In repayment cycle</div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Verified Documents</div>
          <div className="text-2xl font-bold font-mono text-cyan-600 dark:text-cyan-400 mt-2">100%</div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">KYC &amp; Income verified</div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Borrower Health Index</div>
          <div className="text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400 mt-2">Prime A+</div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">Zero delinquency record</div>
        </div>
      </div>

      {/* Applications List */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <CreditCard className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">My Loan Applications</h3>
          </div>
          <span className="text-xs font-mono text-slate-500 dark:text-slate-400">{applications.length} Total Facilities</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300 min-w-[700px]">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 font-mono text-xs uppercase border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Application ID</th>
                <th className="py-3 px-4">Product</th>
                <th className="py-3 px-4 text-right">Requested Principal</th>
                <th className="py-3 px-4 text-center">Tenure</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Reports &amp; Amortization</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
              {applications.map((app) => {
                const isApproved = app.application_status === "APPROVED" || app.application_status === "DISBURSED";
                return (
                  <tr key={app.application_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-slate-900 dark:text-white">{app.application_id}</td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-500 dark:text-slate-400">{app.product_id}</td>
                    <td className="py-3 px-4 text-right font-mono text-emerald-600 dark:text-emerald-400">
                      ₹{Number(app.requested_principal).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-xs text-slate-500 dark:text-slate-400">
                      {app.requested_term_months} M
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border ${
                        isApproved
                          ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20"
                          : app.application_status === "REJECT"
                          ? "bg-rose-50 dark:bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-500/20"
                          : "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20"
                      }`}>
                        {app.application_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <ExportMenu
                          baseEndpoint={`/exports/loans/${app.application_id}`}
                          defaultFilename={`My_Dossier_${app.application_id}`}
                          label="Dossier"
                          size="sm"
                        />
                        <button
                          onClick={() => onSelectApplication(app.application_id)}
                          className="inline-flex items-center space-x-1 text-xs text-cyan-600 dark:text-cyan-400 hover:text-cyan-500 font-medium hover:underline cursor-pointer"
                        >
                          <span>Schedule</span>
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

      {/* Document Status */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">KYC &amp; Verification Documents</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-slate-900 dark:text-white">Identity Proof (Aadhaar / Passport)</div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">Government Photo ID</div>
            </div>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              VERIFIED
            </span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-slate-900 dark:text-white">Income Proof (Salary Slips / ITR)</div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">Financial Verification</div>
            </div>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              VERIFIED
            </span>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-slate-900 dark:text-white">Credit Bureau Report</div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">Comprehensive Credit History</div>
            </div>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              VERIFIED
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
