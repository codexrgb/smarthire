/**
 * SmartHire 2.0 TypeScript Definitions
 * Strictly aligned with FastAPI Pydantic schemas.
 */

export type UserRole = 'candidate' | 'recruiter' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  login_count?: number;
  last_login_at?: string | null;
  is_first_login?: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  database_connected: boolean;
}

export interface DatasetProvenance {
  overall_status: 'demo_synthetic' | 'unknown_unverified' | 'verified_authentic';
  is_demo_mode: boolean;
  ui_badge: string;
  banner_message: string;
  files?: Record<string, {
    status: string;
    reason: string;
    rows?: number;
  }>;
}

export interface ModelStatusResponse {
  models_loaded: Record<string, boolean>;
  best_classifier: string;
  dataset_provenance: DatasetProvenance;
  demo_warning_active: boolean;
}

export interface ResumeValidationResponse {
  is_valid: boolean;
  confidence_category: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_score: number;
  score_label: string;
  is_calibrated_probability: boolean;
  document_type: string;
  rejection_reason?: string | null;
  user_message: string;
  detected_sections: string[];
  structural_signals?: Record<string, any>;
}

export interface ResumeParseResponse {
  resume_id: string;
  original_filename: string;
  file_size_bytes: number;
  sha256: string;
  extracted_skills: string[];
  predicted_category: string;
  category_confidence: number;
  category_probabilities: Record<string, number>;
  status_message: string;
  extracted_text_preview: string;
  validation?: ResumeValidationResponse;
}

export interface MatchScoreRequest {
  resume_text?: string;
  resume_id?: string;
  job_text: string;
  job_skills?: string;
  text_similarity?: number;
}

export interface MatchScoreResponse {
  text_similarity: number;
  skill_overlap: number;
  experience_match: number;
  fit_score: number;
  matched_skills: string[];
  missing_skills: string[];
  score_label: string;
  is_probability: boolean; // Always false — heuristic index guardrail
  explanation: string;
}

export interface JobRecommendItem {
  job_id: string;
  title: string;
  company: string;
  location: string;
  skills: string;
  experience: string;
  salary: string;
  category: string;
  description?: string;
  similarity_score: number;
  skill_match_pct: number;
  fit_score: number;
}

export interface JobRecommendResponse {
  total_results: number;
  recommendations: JobRecommendItem[];
}

export interface CandidateSummary {
  resume_id: string;
  original_filename: string;
  predicted_category: string;
  category_confidence: number;
  file_size_bytes: number;
  uploaded_at: string;
  status: string;
}

export interface ResumeSummaryOut {
  id: string;
  candidate_id?: string | null;
  original_filename: string;
  file_size_bytes: number;
  sha256: string;
  predicted_category: string;
  category_confidence: number;
  uploaded_at: string;
}

export interface ResumeDetailOut {
  id: string;
  candidate_id?: string | null;
  original_filename: string;
  file_size_bytes: number;
  sha256: string;
  predicted_category: string;
  category_confidence: number;
  extracted_skills: string[];
  uploaded_at: string;
  extracted_text_preview: string;
}

export interface RecruiterActionLogRequest {
  action_type: string;
  target_entity_type: string;
  target_entity_id: string;
  details?: string;
}

export interface RecruiterActionOut {
  id: string;
  recruiter_id: string;
  action_type: string;
  target_entity_type: string;
  target_entity_id: string;
  created_at: string;
}

export interface ApiError {
  error?: string;
  detail?: string | Array<{ msg: string; loc: string[] }>;
  message?: string;
  status?: number;
}
