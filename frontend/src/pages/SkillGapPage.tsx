import React, { useState } from 'react';
import { TrendingUp, CheckCircle, XCircle, BookOpen } from 'lucide-react';
import { calculateMatchScore } from '../api';
import type { MatchScoreResponse } from '../api/types';
import { SkillPill } from '../components/common/SkillPill';
import { Alert } from '../components/common/Alert';

export const SkillGapPage: React.FC = () => {
  const [candidateSkillsInput, setCandidateSkillsInput] = useState<string>(
    'Python, SQL, Pandas, NumPy, Scikit-learn, Git, Docker'
  );
  const [targetSkillsInput, setTargetSkillsInput] = useState<string>(
    'Python, SQL, AWS, Kubernetes, Scikit-learn, PyTorch, CI/CD, Docker'
  );
  const [result, setResult] = useState<MatchScoreResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleAnalyzeGap = async () => {
    setErrorMsg(null);
    if (!candidateSkillsInput.trim() || !targetSkillsInput.trim()) {
      setErrorMsg('Please provide both candidate skills and required job skills.');
      return;
    }

    setLoading(true);
    try {
      const res = await calculateMatchScore({
        resume_text: `Skills: ${candidateSkillsInput.trim()}`,
        job_text: `Requirements: ${targetSkillsInput.trim()}`,
        job_skills: targetSkillsInput.trim(),
      });
      setResult(res);
    } catch {
      setErrorMsg('Failed to analyze skill gap. Please check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Technical Skill-Gap Analysis
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Isolate candidate competencies against role requirements to identify targeted career
          upskilling priorities.
        </p>
      </div>

      {errorMsg && (
        <Alert type="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Input Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs transition-colors">
          <label htmlFor="candidate-skills-input" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Candidate Current Skills
          </label>
          <textarea
            id="candidate-skills-input"
            rows={5}
            value={candidateSkillsInput}
            onChange={(e) => setCandidateSkillsInput(e.target.value)}
            placeholder="Comma-separated skills (e.g. Python, SQL, Docker, React)..."
            className="w-full p-3 border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-lg text-sm placeholder-slate-400 dark:placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 font-mono"
          />
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-xs transition-colors">
          <label htmlFor="target-role-skills-input" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Target Role Required Skills
          </label>
          <textarea
            id="target-role-skills-input"
            rows={5}
            value={targetSkillsInput}
            onChange={(e) => setTargetSkillsInput(e.target.value)}
            placeholder="Comma-separated required skills (e.g. AWS, Kubernetes, PyTorch)..."
            className="w-full p-3 border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-lg text-sm placeholder-slate-400 dark:placeholder-slate-500 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 font-mono"
          />
        </div>
      </div>

      <div className="text-center">
        <button
          type="button"
          onClick={handleAnalyzeGap}
          disabled={loading}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
        >
          <TrendingUp className="h-4 w-4" />
          <span>{loading ? 'Analyzing Gap...' : 'Run Skill-Gap Evaluation'}</span>
        </button>
      </div>

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs transition-colors">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-6">
              <div>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Overlap Ratio
                </span>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                  {(result.skill_overlap * 100).toFixed(1)}% Skill Alignment
                </h3>
              </div>

              <div className="text-right">
                <span className="text-xs text-slate-400 dark:text-slate-500 block">Jaccard Overlap</span>
                <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                  {result.matched_skills.length} of{' '}
                  {result.matched_skills.length + result.missing_skills.length} Skills
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Matched Skills */}
              <div className="p-5 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-emerald-950 dark:text-emerald-200 text-sm flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    <span>Matched Competencies ({result.matched_skills.length})</span>
                  </h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.matched_skills.length > 0 ? (
                    result.matched_skills.map((skill) => (
                      <SkillPill key={skill} name={skill} variant="matched" />
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 dark:text-slate-400">None detected in candidate text.</p>
                  )}
                </div>
              </div>

              {/* Missing Skills */}
              <div className="p-5 rounded-xl bg-rose-50/50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/60">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-rose-950 dark:text-rose-200 text-sm flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                    <span>Missing Requirements ({result.missing_skills.length})</span>
                  </h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.missing_skills.length > 0 ? (
                    result.missing_skills.map((skill) => (
                      <SkillPill key={skill} name={skill} variant="missing" />
                    ))
                  ) : (
                    <p className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">
                      Zero skill gaps detected! 100% requirements met.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Upskilling Advice */}
            {result.missing_skills.length > 0 && (
              <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl">
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 rounded-lg bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="h-4 w-4" />
                  </div>
                  <div>
                    <h5 className="text-sm font-semibold text-slate-900 dark:text-white">
                      Recommended Next Learning Goals
                    </h5>
                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                      Focusing your study on{' '}
                      <strong>{result.missing_skills.slice(0, 3).join(', ')}</strong> will
                      substantially improve compatibility for this target career profile.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
