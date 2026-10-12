/**
 * Client-side API client for ClassLens backend services.
 */

export interface Assessment {
  id: string;
  class_id: string;
  organization_id: string;
  title: string;
  status: string;
  question: {
    problem_reference_id: string;
    question_text: string;
    latex_formula: string;
    expected_answer: string;
    accepted_methods: string[];
  };
  total_responses: number;
  reviewed_responses: number;
  created_at: string;
}

export interface StudentResponse {
  id: string;
  assessment_id: string;
  pseudonymous_student_id: string;
  pseudonym_label: string;
  source_filename: string;
  image_mime_type: string;
  upload_status: string;
  task_status: string;
  answer_status: string;
  reasoning_status: string;
  teacher_review_status: string;
  is_compensatory_error: boolean;
  needs_teacher_review: boolean;
  misconception_taxonomy_id?: string;
  teacher_override_taxonomy_id?: string;
  teacher_notes?: string;
  analysis_data?: any;
}

export interface VerifiedStep {
  step_number: number;
  operation: string;
  expected_result: number;
  observed_result?: number;
  is_correct: boolean;
  evidence_citation: string;
  evidence_status?: "supported" | "partially_supported" | "insufficient_evidence";
  verification_status?: "verified_valid" | "verified_error" | "unverifiable";
}

export interface FirstSupportedError {
  step_number: number;
  error_type: string;
  observed_behavior: string;
  expected_behavior: string;
  explanation: string;
}

export interface StudentAnalysisDetail {
  response_id: string;
  pseudonym_label?: string;
  quality_status: string;
  upload_status?: string;
  answer_status: string;
  reasoning_status: string;
  is_compensatory_error: boolean;
  needs_teacher_review: boolean;
  teacher_review_reason?: string;
  teacher_review_status?: string;
  teacher_override_taxonomy_id?: string;
  teacher_notes?: string;
  visual_evidence: {
    confidence: number;
    has_number_line: boolean;
    final_answer_marked?: string;
    ambiguities?: string[];
    requires_teacher_review?: boolean;
    teacher_review_reason?: string;
    observations: Array<{
      kind: string;
      value: string;
      confidence: number;
      start_pos?: number;
      end_pos?: number;
      direction?: string;
      stated_magnitude?: number;
    }>;
  };
  candidate_hypotheses: {
    detected_strategy: string;
    reasoning_completeness: string;
    evidence_support?: "supported" | "partially_supported" | "insufficient_evidence";
    hypotheses: Array<{
      hypothesis_id: string;
      starting_point: number;
      strategy_description: string;
      step_sequence: string[];
      is_valid_alternative_path: boolean;
      confidence?: number;
    }>;
  };
  diagnosis: {
    answer_status: string;
    reasoning_status: string;
    inferred_final_answer?: string;
    misconception_taxonomy_id?: string;
    taxonomy_title?: string;
    is_compensatory_error: boolean;
    confidence: number;
    evidence_sufficiency?: "sufficient" | "partial" | "insufficient";
    diagnostic_explanation?: string;
    verified_steps: Array<VerifiedStep>;
    first_supported_error?: FirstSupportedError;
  };
  critic_audit: {
    approved: boolean;
    confidence?: number;
    evidence_grounded?: boolean;
    contradiction_detected?: boolean;
    reinterpretation_needed: boolean;
    discrepancy_notes: string[];
    requires_teacher_review: boolean;
    teacher_review_reason?: string;
    audit_verdict?: "audit_passed" | "review_required" | "audit_rejected";
  };
  is_mock: boolean;
  model_version: string;
}

export interface MisconceptionCluster {
  taxonomy_id: string;
  title: string;
  affected_count: number;
  affected_percentage: number;
  teacher_confirmed_count: number;
  ai_proposed_count: number;
  sample_response_ids: string[];
}

export interface CohortStatistics {
  total_responses: number;
  correct_count: number;
  correct_percentage: number;
  error_count: number;
  error_percentage: number;
  incomplete_count: number;
  incomplete_percentage: number;
  unreadable_count: number;
  unreadable_percentage: number;
  compensatory_errors_count: number;
  needs_teacher_review_count: number;
  insufficient_evidence_count?: number;
  insufficient_evidence_percentage?: number;
  misconception_clusters: MisconceptionCluster[];
}

export interface DifferentiatedAction {
  target_misconception_id: string;
  action_type: "concrete_manipulative" | "worked_example" | "guided_inquiry";
  title: string;
  instructional_steps: string[];
  student_count_affected: number;
}

export interface ExitTicketItem {
  question_number: number;
  prompt: string;
  target_misconception: string;
  expected_answer: string;
  sympy_verified: boolean;
}

export interface CohortInsights {
  assessment_id: string;
  statistics: CohortStatistics;
  intelligence: {
    executive_narrative: string;
    dominant_misconceptions: string[];
    differentiated_actions: DifferentiatedAction[];
    formative_exit_ticket: ExitTicketItem[];
  };
}

export interface AuditEvent {
  id: string;
  assessment_id: string;
  response_id: string;
  teacher_id: string;
  action: string;
  old_state: any;
  new_state: any;
  notes?: string;
  timestamp: string;
}

const API_BASE = "/api/v1";

async function fetchWithCsrf(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  headers.set("X-Requested-With", "ClassLens");

  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  return res;
}

export const api = {
  async ensureDemoSession() {
    const res = await fetchWithCsrf(`${API_BASE}/auth/google`, {
      method: "POST",
      body: JSON.stringify({ demo_mode: true }),
    });
    return res.json();
  },

  async listAssessments(): Promise<Assessment[]> {
    const res = await fetchWithCsrf(`${API_BASE}/assessments`);
    if (!res.ok) throw new Error("Failed to load assessments");
    return res.json();
  },

  async getAssessment(id: string): Promise<Assessment> {
    const res = await fetchWithCsrf(`${API_BASE}/assessments/${id}`);
    if (!res.ok) throw new Error("Failed to load assessment");
    return res.json();
  },

  async importDemoResponses(id: string) {
    const res = await fetchWithCsrf(`${API_BASE}/assessments/${id}/demo-import`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to import demo responses");
    return res.json();
  },

  async listResponses(assessmentId: string): Promise<StudentResponse[]> {
    const res = await fetchWithCsrf(`${API_BASE}/assessments/${assessmentId}/responses`);
    if (!res.ok) throw new Error("Failed to list responses");
    return res.json();
  },

  async triggerAnalysis(assessmentId: string, idempotencyKey?: string) {
    const res = await fetchWithCsrf(`${API_BASE}/assessments/${assessmentId}/analyze`, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: idempotencyKey }),
    });
    if (!res.ok) throw new Error("Failed to trigger analysis");
    return res.json();
  },

  async getAnalysisStatus(assessmentId: string) {
    const res = await fetchWithCsrf(`${API_BASE}/assessments/${assessmentId}/status`);
    if (!res.ok) throw new Error("Failed to fetch status");
    return res.json();
  },

  async getResponseDetail(responseId: string): Promise<StudentAnalysisDetail> {
    const res = await fetchWithCsrf(`${API_BASE}/responses/${responseId}`);
    if (!res.ok) throw new Error("Failed to load response detail");
    return res.json();
  },

  async submitReview(responseId: string, decision: string, overrideTaxonomyId?: string, notes?: string) {
    const res = await fetchWithCsrf(`${API_BASE}/responses/${responseId}/review`, {
      method: "PUT",
      body: JSON.stringify({
        decision,
        override_misconception_id: overrideTaxonomyId,
        notes,
      }),
    });
    if (!res.ok) throw new Error("Failed to submit review");
    return res.json();
  },

  async getAuditTrail(responseId: string): Promise<AuditEvent[]> {
    const res = await fetchWithCsrf(`${API_BASE}/responses/${responseId}/audit-trail`);
    if (!res.ok) throw new Error("Failed to fetch audit trail");
    return res.json();
  },

  async getCohortInsights(assessmentId: string): Promise<CohortInsights> {
    const res = await fetchWithCsrf(`${API_BASE}/assessments/${assessmentId}/insights`);
    if (!res.ok) throw new Error("Failed to fetch cohort insights");
    return res.json();
  },

  // --------------------------------------------------------------------------
  // Development-Only Gemini Test Lab Methods
  // --------------------------------------------------------------------------
  async getDevStatus(): Promise<DevStatusResponse> {
    const res = await fetchWithCsrf(`${API_BASE}/dev/status`);
    if (!res.ok) throw new Error("Failed to fetch development status");
    return res.json();
  },

  getSyntheticFixtureImageUrl(fixtureId: string): string {
    return `${API_BASE}/dev/synthetic-fixtures/${encodeURIComponent(fixtureId)}/image`;
  },

  async analyzeSynthetic(
    fixtureId: string,
    ruleExpr: string = "-6 + 12 - 4",
    targetValue: number = 2.0
  ): Promise<SyntheticAnalysisResponse> {
    const res = await fetchWithCsrf(`${API_BASE}/dev/analyze-synthetic`, {
      method: "POST",
      body: JSON.stringify({
        fixture_id: fixtureId,
        rule_expr: ruleExpr,
        target_value: targetValue,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Analysis failed with status ${res.status}`);
    }
    return res.json();
  },
};

export interface DevStatusResponse {
  environment: string;
  ai_mode: string;
  live_inference_enabled: boolean;
  is_live_mode: boolean;
  model: string;
  project: string;
  location: string;
  use_vertexai: boolean;
  max_calls: number;
  calls_used: number;
  calls_remaining: number;
  authorized_fixtures: Array<{
    id: string;
    name: string;
    description: string;
    category: string;
    expected_answer?: string | null;
    expected_reasoning: string;
    filename: string;
  }>;
}

export interface SyntheticAnalysisResponse {
  fixture_id: string;
  mode: "mock" | "live";
  model_version: string;
  is_mock: boolean;
  execution_latency_ms: number;
  tokens_consumed: number;
  cost_estimate_usd?: number | null;
  live_telemetry?: Record<string, any> | null;
  calls_used: number;
  calls_remaining: number;
  analysis: any;
}
