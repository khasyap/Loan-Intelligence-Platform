import {
  ExecutiveKPIs,
  RiskAnalytics,
  OperationsAnalytics,
  AnomalyEvaluation,
  GroundTruthItem,
  ApplicationItem,
  ProductItem,
  RepaymentDetails,
  UserProfile,
  UserRole
} from "../types";

const API_BASE = typeof window !== "undefined" && window.location.port === "5173" 
  ? "http://127.0.0.1:8000/api/v1" 
  : "/api/v1";

let currentToken: string | null = typeof window !== "undefined" ? localStorage.getItem("lip_auth_token") : null;

export function setAuthToken(token: string | null) {
  currentToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem("lip_auth_token", token);
    } else {
      localStorage.removeItem("lip_auth_token");
    }
  }
}

export function getAuthToken(): string | null {
  return currentToken;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (currentToken) {
    headers["Authorization"] = `Bearer ${currentToken}`;
  }
  return headers;
}

export async function loginUser(email: string, password: string): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Invalid credentials" }));
    throw new Error(err.detail || "Authentication failed");
  }
  const data = await res.json();
  setAuthToken(data.access_token);
  return {
    email,
    name: data.name,
    role: data.role as UserRole,
    applicant_id: data.applicant_id,
    access_token: data.access_token
  };
}

export async function fetchCurrentUser(): Promise<UserProfile | null> {
  if (!currentToken) return null;
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: authHeaders()
  });
  if (!res.ok) {
    setAuthToken(null);
    return null;
  }
  const data = await res.json();
  return {
    email: data.sub || data.email,
    name: data.name,
    role: data.role as UserRole,
    applicant_id: data.applicant_id,
    access_token: currentToken
  };
}

export async function fetchExecutiveKPIs(): Promise<ExecutiveKPIs> {
  const res = await fetch(`${API_BASE}/analytics/executive`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load executive KPIs");
  return res.json();
}

export async function fetchRiskAnalytics(): Promise<RiskAnalytics> {
  const res = await fetch(`${API_BASE}/analytics/risk`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load risk analytics");
  return res.json();
}

export async function fetchOperationsAnalytics(): Promise<OperationsAnalytics> {
  const res = await fetch(`${API_BASE}/analytics/operations`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load operations analytics");
  return res.json();
}

export async function fetchAnomalyEvaluation(): Promise<AnomalyEvaluation> {
  const res = await fetch(`${API_BASE}/anomalies/evaluation`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load anomaly evaluation");
  return res.json();
}

export async function fetchGroundTruth(): Promise<GroundTruthItem[]> {
  const res = await fetch(`${API_BASE}/anomalies/ground-truth`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load ground truth");
  return res.json();
}

export async function fetchApplications(status?: string): Promise<ApplicationItem[]> {
  const url = status ? `${API_BASE}/applications?status=${status}&limit=100` : `${API_BASE}/applications?limit=100`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load applications");
  return res.json();
}

export async function fetchApplicationDetail(applicationId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/applications/${applicationId}`, { headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to load application details" }));
    throw new Error(err.detail || `Failed to load application details (${res.status})`);
  }
  return res.json();
}

export async function fetchProducts(): Promise<ProductItem[]> {
  const res = await fetch(`${API_BASE}/products`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

export async function fetchRepayments(applicationId: string): Promise<RepaymentDetails> {
  const res = await fetch(`${API_BASE}/repayments/${applicationId}`, { headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to load repayment schedule" }));
    throw new Error(err.detail || `Failed to load repayment schedule (${res.status})`);
  }
  return res.json();
}

export async function submitApplication(payload: {
  applicant_id: string;
  product_id: string;
  requested_principal: number;
  requested_term_months: number;
  submission_channel: string;
}) {
  const res = await fetch(`${API_BASE}/applications`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Submission failed" }));
    throw new Error(err.detail || "Application submission failed");
  }
  return res.json();
}

export async function fetchDocuments(applicationId?: string): Promise<any[]> {
  const url = applicationId ? `${API_BASE}/documents?application_id=${applicationId}` : `${API_BASE}/documents`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load documents");
  return res.json();
}

export async function verifyDocument(documentId: string, verificationStatus: string, reason?: string) {
  const res = await fetch(`${API_BASE}/documents/${documentId}/verify`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ verification_status: verificationStatus, reason: reason || "Manual Verification" })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Verification failed" }));
    throw new Error(err.detail || "Document verification failed");
  }
  return res.json();
}

export async function submitDecisionOverride(decisionId: string, newStatus: string, reason: string) {
  const res = await fetch(`${API_BASE}/decisions/${decisionId}/override`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ new_status: newStatus, reason })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Override failed" }));
    throw new Error(err.detail || "Decision override failed");
  }
  return res.json();
}

export async function fetchDisbursementEligibility(applicationId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/disbursements/${applicationId}/eligibility`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to check disbursement eligibility");
  return res.json();
}

export async function downloadReport(endpoint: string, fallbackFilename: string): Promise<void> {
  const url = `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({ detail: "Export generation failed" }));
    throw new Error(errorJson.detail || `Export failed with status ${res.status}`);
  }

  let filename = fallbackFilename;
  const disposition = res.headers.get("Content-Disposition");
  if (disposition && disposition.includes("filename=")) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(downloadUrl);
  document.body.removeChild(a);
}
