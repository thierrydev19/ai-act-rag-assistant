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
  answer_simple: string;
  checks: string[];
  sources: string[];
  limits: string[];
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
  return parseJsonOrThrow<DemoCase[]>(response);
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return parseJsonOrThrow<AskResponse>(response);
}

