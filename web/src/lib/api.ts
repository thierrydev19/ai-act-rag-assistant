export type DemoCase = {
  case_id: string;
  title: string;
  question: string;
  expected_refusal: boolean;
};

export type AskResponse = {
  question: string;
  retrieval_status: string;
  retrieval_message: string;
  refusal: boolean;
  intent: string;
  business_case: string;
  answer_simple: string;
  business_impact: string[];
  checks: string[];
  uncertainties: string[];
  sources: string[];
  limits: string[];
  context_needed: boolean;
  context_questions: string[];
  context_used: Record<string, string>;
};

export type AskContext = {
  usage_case?: string;
  company_role?: string;
  impact_level?: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

async function parseJsonOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchDemoCases(): Promise<DemoCase[]> {
  const response = await fetch(`${API_BASE_URL}/api/demo-cases`, {
    method: "GET",
    cache: "no-store",
  });
  const payload = await parseJsonOrThrow<DemoCase[]>(response);
  if (!Array.isArray(payload) || payload.length === 0) {
    throw new Error("Aucun cas de demo recu depuis l'API.");
  }
  return payload;
}

export async function askQuestion(
  question: string,
  context?: AskContext,
): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, ...(context || {}) }),
  });
  return parseJsonOrThrow<AskResponse>(response);
}

