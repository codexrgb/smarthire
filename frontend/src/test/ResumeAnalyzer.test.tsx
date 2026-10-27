import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ResumeAnalyzerPage } from '../pages/ResumeAnalyzerPage';

describe('ResumeAnalyzerPage validation', () => {
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
});
