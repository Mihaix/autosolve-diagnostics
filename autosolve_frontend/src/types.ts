export interface DiagnosticRequest {
  make: string;
  model: string;
  year: number;
  query: string;
}

export interface DiagnosticResponse {
  problem_elaboration: string;
  core_cause: string;
  solution: string;
  sources: string[];
  confidence_score: number;
  is_fallback: boolean;
}

export interface HistoryItem {
  id: string;
  request: DiagnosticRequest;
  response: DiagnosticResponse;
  timestamp: string;
}
