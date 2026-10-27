import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CandidateDashboard } from '../pages/CandidateDashboard';
import { CandidateManagementPage } from '../pages/CandidateManagementPage';
import * as authContext from '../context/AuthContext';
import * as api from '../api';

vi.mock('../api');

describe('Candidate Workflows UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders candidate uploaded resumes and triggers deletion', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: 'cand-1',
        email: 'alice@example.com',
        full_name: 'Alice Candidate',
        role: 'candidate',
        is_active: true,
        created_at: '2026-10-26T00:00:00Z',
      },
      token: 'valid-token',
      isLoading: false,
      isAuthenticated: true,
      isRecruiter: false,
      isCandidate: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      updateProfile: vi.fn(),
    });

    vi.spyOn(api, 'getMyResumes').mockResolvedValue([
      {
        id: 'res-123',
        original_filename: 'alice_software_engineer.pdf',
        file_size_bytes: 2048,
        sha256: 'a1b2c3d4e5',
        predicted_category: 'Software Engineering',
        category_confidence: 0.94,
        uploaded_at: '2026-10-26T12:00:00Z',
      },
    ]);

    vi.spyOn(api, 'getJobs').mockResolvedValue([]);
    vi.spyOn(api, 'deleteResume').mockResolvedValue({ status: 'success', message: 'Deleted' });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <MemoryRouter>
        <CandidateDashboard />
      </MemoryRouter>
    );

    // Verify resume item is displayed
    await waitFor(() => {
      expect(screen.getByText('alice_software_engineer.pdf')).toBeInTheDocument();
      expect(screen.getByText(/Software Engineering/)).toBeInTheDocument();
    });

    // Click delete
    const deleteBtn = screen.getByTitle('Delete resume');
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(api.deleteResume).toHaveBeenCalledWith('res-123');
      expect(screen.getByText(/Resume document deleted successfully/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when candidate has no uploaded resumes', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: 'cand-2',
        email: 'bob@example.com',
        full_name: 'Bob Candidate',
        role: 'candidate',
        is_active: true,
        created_at: '2026-10-26T00:00:00Z',
      },
      token: 'valid-token',
      isLoading: false,
      isAuthenticated: true,
      isRecruiter: false,
      isCandidate: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      updateProfile: vi.fn(),
    });

    vi.spyOn(api, 'getMyResumes').mockResolvedValue([]);
    vi.spyOn(api, 'getJobs').mockResolvedValue([]);

    render(
      <MemoryRouter>
        <CandidateDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No resumes uploaded yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Upload Your First Resume/i)).toBeInTheDocument();
    });
  });

  it('displays first-time greeting and instructions for newly registered candidates', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: 'cand-new',
        email: 'divya@example.com',
        full_name: 'divya sharma',
        role: 'candidate',
        is_active: true,
        is_first_login: true,
        login_count: 1,
        created_at: '2026-10-27T00:00:00Z',
      },
      token: 'valid-token',
      isLoading: false,
      isAuthenticated: true,
      isRecruiter: false,
      isCandidate: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      updateProfile: vi.fn(),
    });

    vi.spyOn(api, 'getMyResumes').mockResolvedValue([]);
    vi.spyOn(api, 'getJobs').mockResolvedValue([]);

    render(
      <MemoryRouter>
        <CandidateDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      // First-time candidate heading: capitalized "divya" -> "Divya"
      expect(screen.getByText('Welcome, Divya!')).toBeInTheDocument();
      // First-time candidate subtext
      expect(
        screen.getByText('Welcome to SmartHire. Upload your resume to discover relevant jobs and analyze your skills.')
      ).toBeInTheDocument();
    });
  });

  it('displays "Welcome back" greeting for returning candidates who logged in previously', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: 'cand-returning',
        email: 'divya@example.com',
        full_name: 'divya sharma',
        role: 'candidate',
        is_active: true,
        is_first_login: false,
        login_count: 3,
        created_at: '2026-10-25T00:00:00Z',
      },
      token: 'valid-token',
      isLoading: false,
      isAuthenticated: true,
      isRecruiter: false,
      isCandidate: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      updateProfile: vi.fn(),
    });

    vi.spyOn(api, 'getMyResumes').mockResolvedValue([]);
    vi.spyOn(api, 'getJobs').mockResolvedValue([]);

    render(
      <MemoryRouter>
        <CandidateDashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Welcome back, Divya!')).toBeInTheDocument();
      expect(
        screen.getByText(/extract validated technical skills, classify into industry categories/i)
      ).toBeInTheDocument();
    });
  });
});

describe('Recruiter Evaluation Workflow UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays candidate evaluation status and logs recruiter actions', async () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: 'rec-1',
        email: 'recruiter@example.com',
        full_name: 'Jane Recruiter',
        role: 'recruiter',
        is_active: true,
        created_at: '2026-10-26T00:00:00Z',
      },
      token: 'valid-recruiter-token',
      isLoading: false,
      isAuthenticated: true,
      isRecruiter: true,
      isCandidate: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
      updateProfile: vi.fn(),
    });

    vi.spyOn(api, 'getRecruiterCandidates').mockResolvedValue([
      {
        resume_id: 'cand-resume-1',
        original_filename: 'candidate_cv.pdf',
        predicted_category: 'Data Science',
        category_confidence: 0.91,
        file_size_bytes: 4096,
        uploaded_at: '2026-10-26T15:00:00Z',
        status: 'pending',
      },
    ]);

    vi.spyOn(api, 'logRecruiterAction').mockResolvedValue({
      id: 'act-1',
      recruiter_id: 'rec-1',
      action_type: 'shortlist',
      target_entity_type: 'resume',
      target_entity_id: 'cand-resume-1',
      created_at: '2026-10-26T15:30:00Z',
    });

    render(
      <MemoryRouter>
        <CandidateManagementPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('candidate_cv.pdf')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    // Shortlist candidate
    const shortlistBtn = screen.getByRole('button', { name: /shortlist/i });
    fireEvent.click(shortlistBtn);

    await waitFor(() => {
      expect(api.logRecruiterAction).toHaveBeenCalledWith(
        expect.objectContaining({
          action_type: 'shortlist',
          target_entity_id: 'cand-resume-1',
        })
      );
      expect(screen.getByText(/shortlisted successfully/i)).toBeInTheDocument();
    });
  });
});
