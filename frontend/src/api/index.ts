/**
 * SmartHire 2.0 API Operations
 */

import { apiClient } from './client';
import type {
  HealthResponse,
  ModelStatusResponse,
  ResumeParseResponse,
  ResumeSummaryOut,
  ResumeDetailOut,
  MatchScoreRequest,
  MatchScoreResponse,
  JobRecommendResponse,
  JobRecommendItem,
  User,
  TokenResponse,
  CandidateSummary,
  RecruiterActionLogRequest,
  RecruiterActionOut,
} from './types';

// Health & System Status
export const getHealth = async (): Promise<HealthResponse> => {
  return apiClient<HealthResponse>('/health');
};

export const getModelsStatus = async (): Promise<ModelStatusResponse> => {
  return apiClient<ModelStatusResponse>('/api/v1/models/status');
};

// Resume Parsing
export const parseResume = async (options: {
  file?: File;
  rawText?: string;
  filename?: string;
}): Promise<ResumeParseResponse> => {
  const formData = new FormData();
  if (options.file) {
    formData.append('file', options.file, options.file.name);
  }
  if (options.rawText) {
    formData.append('raw_text', options.rawText);
  }
  if (options.filename) {
    formData.append('filename', options.filename);
  }

  return apiClient<ResumeParseResponse>('/api/v1/resumes/parse', {
    method: 'POST',
    body: formData,
  });
};

export const getMyResumes = async (): Promise<ResumeSummaryOut[]> => {
  return apiClient<ResumeSummaryOut[]>('/api/v1/resumes/my-resumes');
};

export const getResumeById = async (resumeId: string): Promise<ResumeDetailOut> => {
  return apiClient<ResumeDetailOut>(`/api/v1/resumes/${resumeId}`);
};

export const deleteResume = async (resumeId: string): Promise<{ status: string; message: string }> => {
  return apiClient<{ status: string; message: string }>(`/api/v1/resumes/${resumeId}`, {
    method: 'DELETE',
  });
};

// Candidate-Job Matching (Heuristic Compatibility Index)
export const calculateMatchScore = async (
  payload: MatchScoreRequest
): Promise<MatchScoreResponse> => {
  return apiClient<MatchScoreResponse>('/api/v1/matching/score', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

// Job Recommendations
export const recommendJobs = async (payload: {
  resume_text?: string;
  resume_id?: string;
  top_n?: number;
  category_filter?: string | null;
}): Promise<JobRecommendResponse> => {
  return apiClient<JobRecommendResponse>('/api/v1/jobs/recommend', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

// Job Explorer
export const getJobs = async (params?: {
  title?: string;
  location?: string;
  limit?: number;
}): Promise<JobRecommendItem[]> => {
  return apiClient<JobRecommendItem[]>('/api/v1/jobs', {
    params: {
      title: params?.title,
      location: params?.location,
      limit: params?.limit || 20,
    },
  });
};

// Authentication
export const registerUser = async (payload: {
  email: string;
  password: string;
  full_name: string;
  role: 'candidate' | 'recruiter';
}): Promise<User> => {
  return apiClient<User>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const loginUser = async (payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> => {
  return apiClient<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const getCurrentUserProfile = async (): Promise<User> => {
  return apiClient<User>('/api/v1/auth/me');
};

// Recruiter Portal (RBAC Protected)
export const getRecruiterCandidates = async (): Promise<CandidateSummary[]> => {
  return apiClient<CandidateSummary[]>('/api/v1/recruiter/candidates');
};

export const logRecruiterAction = async (
  payload: RecruiterActionLogRequest
): Promise<RecruiterActionOut> => {
  return apiClient<RecruiterActionOut>('/api/v1/recruiter/actions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const getRecruiterActions = async (): Promise<RecruiterActionOut[]> => {
  return apiClient<RecruiterActionOut[]>('/api/v1/recruiter/actions');
};
