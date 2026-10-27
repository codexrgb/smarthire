import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CandidateManagementPage } from '../pages/CandidateManagementPage';
import * as authContext from '../context/AuthContext';

describe('Role-Based Access Control (RBAC)', () => {
  it('blocks non-recruiter candidates from Candidate Management with 403 alert', () => {
    vi.spyOn(authContext, 'useAuth').mockReturnValue({
      user: {
        id: '123',
        email: 'candidate@example.com',
        full_name: 'Test Candidate',
        role: 'candidate',
        is_active: true,
        created_at: '2026-10-26T00:00:00Z',
      },
      token: 'fake-candidate-token',
      isLoading: false,
      isAuthenticated: true,
      isRecruiter: false,
      isCandidate: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <MemoryRouter>
        <CandidateManagementPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
    expect(
      screen.getByText(/protected by Role-Based Access Control/i)
    ).toBeInTheDocument();
  });
});
