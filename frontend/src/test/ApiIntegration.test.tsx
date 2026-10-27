import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getHealth, calculateMatchScore, getJobs } from '../api';
import { setAuthToken } from '../api/client';

describe('API Integration & Client Service', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    setAuthToken(null);
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('fetches system health successfully', async () => {
    const mockHealth = {
      status: 'healthy',
      version: '2.0.0',
      timestamp: '2026-10-26T22:00:00Z',
      database_connected: true,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockHealth,
    });

    const result = await getHealth();
    expect(result.status).toBe('healthy');
    expect(result.database_connected).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.any(Object)
    );
  });

  it('calculates candidate-job match score and parses heuristic index', async () => {
    const mockMatch = {
      text_similarity: 0.75,
      skill_overlap: 0.8,
      experience_match: 0.9,
      fit_score: 79.5,
      matched_skills: ['Python', 'SQL'],
      missing_skills: ['AWS'],
      score_label: 'Heuristic Compatibility Index',
      is_probability: false,
      explanation: 'Heuristic compatibility score.',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockMatch,
    });

    const result = await calculateMatchScore({
      resume_text: 'Python developer with SQL',
      job_text: 'Python developer with SQL and AWS',
    });

    expect(result.fit_score).toBe(79.5);
    expect(result.is_probability).toBe(false);
    expect(result.score_label).toBe('Heuristic Compatibility Index');
  });

  it('throws parsed ApiError on non-200 responses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'Resume text too short (minimum 10 characters required).' }),
    });

    await expect(
      calculateMatchScore({
        resume_text: 'Short',
        job_text: 'Short',
      })
    ).rejects.toEqual(
      expect.objectContaining({
        status: 400,
        detail: 'Resume text too short (minimum 10 characters required).',
      })
    );
  });

  it('appends query parameters when fetching jobs list', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });

    await getJobs({ title: 'Engineer', location: 'Remote', limit: 10 });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/jobs\?title=Engineer&location=Remote&limit=10/),
      expect.any(Object)
    );
  });
});
