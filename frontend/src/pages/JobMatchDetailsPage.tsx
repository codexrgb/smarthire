import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  GitCompare,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';
import { calculateMatchScore } from '../api';
import type { MatchScoreResponse, ApiError } from '../api/types';
import { HeuristicBadge } from '../components/common/HeuristicBadge';
import { SkillPill } from '../components/common/SkillPill';
import { Alert } from '../components/common/Alert';

export const JobMatchDetailsPage: React.FC = () => {
  const [searchParams] = useSearchParams();

  const [resumeText, setResumeText] = useState<string>(
    searchParams.get('resume_text') ||
      'Experienced Python developer with machine learning, SQL, pandas, FastAPI, and Docker pipeline architecture.'
  );
  const [jobText, setJobText] = useState<string>(
    searchParams.get('job_text') ||
      'Senior Python Developer seeking expertise in machine learning algorithms, SQL databases, Docker, and AWS cloud.'
  );
  const jobTitle = searchParams.get('job_title') || 'Senior Python Developer';

  const resumeId = searchParams.get('resume_id') || undefined;
  const textSimParam = searchParams.get('text_sim');
  const textSim = textSimParam ? parseFloat(textSimParam) : undefined;
  const jobSkills = searchParams.get('job_skills') || undefined;

  const [matchResult, setMatchResult] = useState<MatchScoreResponse | null>(null);
  const [isCalculating, setIsCalculating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCalculateMatch = React.useCallback(async () => {
    setErrorMsg(null);
    if (resumeText.trim().length < 10 || jobText.trim().length < 10) {
      setErrorMsg('Both candidate text and job description must contain at least 10 characters.');
      return;
    }

    setIsCalculating(true);
    try {
      const res = await calculateMatchScore({
        resume_id: resumeId,
        resume_text: resumeText.trim(),
        job_text: jobText.trim(),
        job_skills: jobSkills || (jobText.includes(',') && jobText.length < 300 ? jobText.trim() : undefined),
        text_similarity: textSim,
      });
      setMatchResult(res);
    } catch (err: any) {
      const apiErr = err as ApiError;
      setErrorMsg(typeof apiErr.detail === 'string' ? apiErr.detail : 'Calculation failed.');
    } finally {
      setIsCalculating(false);
    }
  }, [resumeText, jobText]);

  useEffect(() => {
    // Run initial comparison on mount
    handleCalculateMatch();
  }, [handleCalculateMatch]);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Job Match Compatibility Details
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Deterministic 3-factor heuristic score comparing candidate resume profile against target
          job requirements.
        </p>
      </div>

      {errorMsg && (
        <Alert type="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Inputs Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs transition-colors">
          <label htmlFor="resume-text-input" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Candidate Resume Profile
          </label>
          <textarea
            id="resume-text-input"
            rows={6}
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste candidate experience or resume summary..."
            className="w-full p-3 border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-lg text-xs font-mono placeholder-slate-400 dark:placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
          />
          <div className="flex justify-between text-xs text-slate-400 dark:text-slate-500 mt-1">
            <span>{resumeText.length} characters</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs transition-colors">
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="job-description-input" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Target Job Posting / Requirements
            </label>
            {jobTitle && (
              <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400 truncate max-w-[150px]">
                {jobTitle}
              </span>
            )}
          </div>
          <textarea
            id="job-description-input"
            rows={6}
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste target job description or required skills..."
            className="w-full p-3 border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-lg text-xs font-mono placeholder-slate-400 dark:placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
          />
          <div className="flex justify-between text-xs text-slate-400 dark:text-slate-500 mt-1">
            <span>{jobText.length} characters</span>
          </div>
        </div>
      </div>

      <div className="text-center">
        <button
          type="button"
          onClick={handleCalculateMatch}
          disabled={isCalculating}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
        >
          <GitCompare className="h-4 w-4" />
          <span>{isCalculating ? 'Computing Overlap...' : 'Recalculate Fit Index'}</span>
        </button>
      </div>

      {/* Match Results Card */}
      {matchResult && (
        <div className="space-y-6">
          {/* Main Fit Index Card */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs transition-colors">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
              <div>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Overall Alignment
                </span>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                  Multi-Factor Compatibility Index
                </h3>
              </div>

              <HeuristicBadge score={matchResult.fit_score} size="lg" />
            </div>

            {/* Mandatory Academic Guardrail Banner */}
            <div className="mt-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs text-slate-600 dark:text-slate-300 flex items-start gap-2">
              <Info className="h-4 w-4 text-slate-400 dark:text-slate-500 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Scientific Disclosure:</strong> {matchResult.explanation} This score is
                explicitly flagged as <code className="bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 px-1 py-0.5 rounded text-[11px]">is_probability: false</code> and
                must not be portrayed as an interview probability.
              </span>
            </div>

            {/* 3 Component Breakdown */}
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span>Text Similarity (50%)</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {(matchResult.text_similarity * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden mt-2">
                  <div
                    className="h-2 rounded-full bg-indigo-600"
                    style={{ width: `${Math.min(100, matchResult.text_similarity * 100)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-2">
                  TF-IDF cosine similarity between resume and job tokens.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span>Skill Overlap (30%)</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {(matchResult.skill_overlap * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden mt-2">
                  <div
                    className="h-2 rounded-full bg-purple-600"
                    style={{ width: `${Math.min(100, matchResult.skill_overlap * 100)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-2">
                  Jaccard set intersection of extracted technical skills.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                  <span>Experience Match (20%)</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {(matchResult.experience_match * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden mt-2">
                  <div
                    className="h-2 rounded-full bg-emerald-600"
                    style={{ width: `${Math.min(100, matchResult.experience_match * 100)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-2">
                  Heuristic seniority alignment (years, lead vs junior).
                </p>
              </div>
            </div>

            {/* Skill Details */}
            <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-xs font-semibold text-emerald-800 dark:text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <span>Matched Competencies ({matchResult.matched_skills.length})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.matched_skills.length > 0 ? (
                    matchResult.matched_skills.map((skill) => (
                      <SkillPill key={skill} name={skill} variant="matched" />
                    ))
                  ) : (
                    <span className="text-xs text-slate-400 dark:text-slate-500">No overlapping skills found.</span>
                  )}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-rose-800 dark:text-rose-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <XCircle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                  <span>Missing Requirements ({matchResult.missing_skills.length})</span>
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {matchResult.missing_skills.length > 0 ? (
                    matchResult.missing_skills.map((skill) => (
                      <SkillPill key={skill} name={skill} variant="missing" />
                    ))
                  ) : (
                    <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                      All required skills present in candidate profile!
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
