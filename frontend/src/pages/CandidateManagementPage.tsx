import React, { useEffect, useState } from 'react';
import {
  Search,
  CheckCircle,
  XCircle,
  FileText,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getRecruiterCandidates, logRecruiterAction } from '../api';
import type { CandidateSummary } from '../api/types';
import { Alert } from '../components/common/Alert';

export const CandidateManagementPage: React.FC = () => {
  const { isRecruiter } = useAuth();
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getRecruiterCandidates();
      setCandidates(data);
    } catch (err: any) {
      setErrorMsg(err.detail || 'Failed to fetch candidate records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isRecruiter) {
      fetchCandidates();
    }
  }, [isRecruiter]);

  const handleAction = async (resumeId: string, actionType: 'shortlist' | 'reject') => {
    try {
      await logRecruiterAction({
        action_type: actionType,
        target_entity_type: 'resume',
        target_entity_id: resumeId,
        details: JSON.stringify({ recorded_at: new Date().toISOString() }),
      });
      setFeedback(`Candidate ${actionType === 'shortlist' ? 'shortlisted' : 'flagged'} successfully. Audit action recorded in database.`);
      setTimeout(() => setFeedback(null), 4000);
    } catch {
      setErrorMsg('Failed to log recruiter action.');
    }
  };

  if (!isRecruiter) {
    return (
      <div className="py-12 max-w-xl mx-auto">
        <Alert type="error" title="Access Denied">
          Candidate records are protected by Role-Based Access Control and require recruiter credentials.
        </Alert>
      </div>
    );
  }

  // Filter candidates
  const categories = ['all', ...Array.from(new Set(candidates.map((c) => c.predicted_category)))];

  const filtered = candidates.filter((c) => {
    const matchesSearch = c.original_filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = categoryFilter === 'all' || c.predicted_category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Candidate Pipeline & Management
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Review parsed candidate profiles, predicted job categories, and maintain compliance
            audit logging.
          </p>
        </div>
      </div>

      {feedback && (
        <Alert type="success" onClose={() => setFeedback(null)}>
          {feedback}
        </Alert>
      )}

      {errorMsg && (
        <Alert type="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 rounded-md shadow-2xs">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="h-4 w-4" />
          </div>
          <input
            type="text"
            placeholder="Search by resume filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white text-slate-700"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={fetchCandidates}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400 text-sm">
            Fetching protected candidate records...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-sm">
            No candidate resumes match the current criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-semibold text-xs uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3.5">Candidate Document</th>
                  <th className="px-6 py-3.5">Predicted Family</th>
                  <th className="px-6 py-3.5">Confidence</th>
                  <th className="px-6 py-3.5">Uploaded</th>
                  <th className="px-6 py-3.5 text-right">Recruiter Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((cand) => (
                  <tr key={cand.resume_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2.5">
                        <FileText className="h-4 w-4 text-indigo-600 flex-shrink-0" />
                        <div>
                          <span className="font-semibold text-slate-900 block truncate max-w-[220px]">
                            {cand.original_filename}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">
                            {(cand.file_size_bytes / 1024).toFixed(1)} KB
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {cand.predicted_category}
                      </span>
                    </td>

                    <td className="px-6 py-4 font-mono font-medium text-slate-800">
                      {(cand.category_confidence * 100).toFixed(1)}%
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(cand.uploaded_at).toLocaleDateString()}
                    </td>

                    <td className="px-6 py-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleAction(cand.resume_id, 'shortlist')}
                          className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors"
                        >
                          <CheckCircle className="h-3.5 w-3.5" />
                          <span>Shortlist</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleAction(cand.resume_id, 'reject')}
                          className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                          <span>Decline</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
