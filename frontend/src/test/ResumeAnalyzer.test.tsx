import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ResumeAnalyzerPage } from '../pages/ResumeAnalyzerPage';
import * as api from '../api';

vi.mock('../api');

describe('ResumeAnalyzerPage validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('validates minimum text length on paste tab', async () => {
    render(
      <MemoryRouter>
        <ResumeAnalyzerPage />
      </MemoryRouter>
    );

    // Switch to paste tab
    const pasteTabBtn = screen.getByText(/Paste Resume Text/i);
    fireEvent.click(pasteTabBtn);

    // Enter short text (<10 chars)
    const textarea = screen.getByPlaceholderText(/Paste the plain text of your resume here/i);
    fireEvent.change(textarea, { target: { value: 'Too short' } });

    // Click run analysis
    const runBtn = screen.getByText(/Run Analysis/i);
    fireEvent.click(runBtn);

    expect(
      await screen.findByText(/Please enter at least 10 characters of resume text/i)
    ).toBeInTheDocument();
  });

  it('rejects unsupported file extensions on file upload', async () => {
    render(
      <MemoryRouter>
        <ResumeAnalyzerPage />
      </MemoryRouter>
    );

    const input = document.getElementById('resume-file') as HTMLInputElement;
    const fakeExeFile = new File(['binary content'], 'exploit.exe', { type: 'application/x-msdownload' });

    fireEvent.change(input, { target: { files: [fakeExeFile] } });

    expect(
      await screen.findByText(/Unsupported file type '\.exe'/i)
    ).toBeInTheDocument();
  });

  it('displays clear feedback when document does not appear to be a resume (e.g. research paper)', async () => {
    vi.spyOn(api, 'parseResume').mockRejectedValue({
      status: 400,
      detail: 'This document does not appear to be a resume. Please upload your resume in PDF or DOCX format.',
    });

    render(
      <MemoryRouter>
        <ResumeAnalyzerPage />
      </MemoryRouter>
    );

    // Switch to paste tab and enter text
    fireEvent.click(screen.getByText(/Paste Resume Text/i));
    const textarea = screen.getByPlaceholderText(/Paste the plain text of your resume here/i);
    fireEvent.change(textarea, { target: { value: 'Deep Residual Learning for Image Recognition Abstract In this paper...' } });

    fireEvent.click(screen.getByText(/Run Analysis/i));

    await waitFor(() => {
      expect(screen.getByText(/Invalid Document/i)).toBeInTheDocument();
      expect(
        screen.getByText(/This document does not appear to be a resume\. Please upload your resume in PDF or DOCX format\./i)
      ).toBeInTheDocument();
    });
  });

  it('displays unreadable document guidance when readable text cannot be extracted', async () => {
    vi.spyOn(api, 'parseResume').mockRejectedValue({
      status: 400,
      detail: 'Readable text could not be extracted from this document. If this is a scanned PDF, please provide a text-searchable PDF, DOCX, or TXT file.',
    });

    render(
      <MemoryRouter>
        <ResumeAnalyzerPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Paste Resume Text/i));
    const textarea = screen.getByPlaceholderText(/Paste the plain text of your resume here/i);
    fireEvent.change(textarea, { target: { value: 'Unreadable scanned document text simulation...' } });

    fireEvent.click(screen.getByText(/Run Analysis/i));

    await waitFor(() => {
      expect(screen.getByText(/Unreadable Document/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Readable text could not be extracted from this document/i)
      ).toBeInTheDocument();
    });
  });

  it('displays uncertain document guidance when document lacks clear structure', async () => {
    vi.spyOn(api, 'parseResume').mockRejectedValue({
      status: 400,
      detail: 'The document could not be verified as a resume. Please upload a clearer or more complete resume in PDF or DOCX format.',
    });

    render(
      <MemoryRouter>
        <ResumeAnalyzerPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Paste Resume Text/i));
    const textarea = screen.getByPlaceholderText(/Paste the plain text of your resume here/i);
    fireEvent.change(textarea, { target: { value: 'Some ambiguous notes about programming...' } });

    fireEvent.click(screen.getByText(/Run Analysis/i));

    await waitFor(() => {
      expect(screen.getByText(/Uncertain Document/i)).toBeInTheDocument();
      expect(
        screen.getByText(/The document could not be verified as a resume\. Please upload a clearer or more complete resume/i)
      ).toBeInTheDocument();
    });
  });

  it('displays validated resume status badge on successful validation and parsing', async () => {
    vi.spyOn(api, 'parseResume').mockResolvedValue({
      resume_id: 'res-valid-99',
      original_filename: 'candidate_resume.pdf',
      file_size_bytes: 4096,
      sha256: 'abc123456789def',
      extracted_skills: ['Python', 'FastAPI', 'Docker'],
      predicted_category: 'Software Engineering',
      category_confidence: 0.96,
      category_probabilities: { 'Software Engineering': 0.96 },
      status_message: 'Resume parsed successfully.',
      extracted_text_preview: 'Alice Candidate - Senior Software Engineer...',
      validation: {
        is_valid: true,
        confidence_category: 'HIGH',
        confidence_score: 0.95,
        score_label: 'Heuristic Validation Index',
        is_calibrated_probability: false,
        document_type: 'resume',
        user_message: 'Resume validated successfully.',
        detected_sections: ['Experience', 'Education', 'Skills'],
      },
    });

    vi.spyOn(api, 'recommendJobs').mockResolvedValue({
      total_results: 1,
      recommendations: [
        {
          job_id: 'job-1',
          title: 'Senior Backend Engineer',
          company: 'TechCorp',
          location: 'San Francisco, CA',
          skills: 'Python, FastAPI, Docker',
          experience: '3-5 years',
          salary: '$140,000',
          category: 'Software Engineering',
          similarity_score: 0.88,
          skill_match_pct: 90.0,
          fit_score: 87.5,
        },
      ],
    });

    render(
      <MemoryRouter>
        <ResumeAnalyzerPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText(/Paste Resume Text/i));
    const textarea = screen.getByPlaceholderText(/Paste the plain text of your resume here/i);
    fireEvent.change(textarea, { target: { value: 'Alice Candidate - Senior Software Engineer with Python and FastAPI...' } });

    fireEvent.click(screen.getByText(/Run Analysis/i));

    await waitFor(() => {
      expect(screen.getByText(/Validated Resume \(HIGH Confidence\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Experience, Education, Skills/i)).toBeInTheDocument();
      expect(screen.getAllByText('Software Engineering').length).toBeGreaterThan(0);
      expect(screen.getByText('Python')).toBeInTheDocument();
    });
  });
});
