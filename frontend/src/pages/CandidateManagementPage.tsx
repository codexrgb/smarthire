import React, { useEffect, useState } from 'react';
import {
  Search,
  CheckCircle,
  XCircle,
  FileText,
  Eye,
  X,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getRecruiterCandidates, logRecruiterAction, getResumeById } from '../api';
import type { CandidateSummary, ResumeDetailOut } from '../api/types';
import { Alert } from '../components/common/Alert';
import { SkillPill } from '../components/common/SkillPill';

export const CandidateManagementPage: React.FC = () => {
  const { isRecruiter } = useAuth();
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Candidate Inspection Modal State
  const [inspectModalOpen, setInspectModalOpen] = useState<boolean>(false);
  const [inspectCandidate, setInspectCandidate] = useState<ResumeDetailOut | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);

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
      // Reflect persisted status in candidate state
      setCandidates((prev) =>
        prev.map((c) => (c.resume_id === resumeId ? { ...c, status: actionType } : c))
      );
      setFeedback(`Candidate ${actionType === 'shortlist' ? 'shortlisted' : 'flagged as declined'} successfully. Audit action recorded in database.`);
      setTimeout(() => setFeedback(null), 4000);
    } catch {
      setErrorMsg('Failed to log recruiter action.');
    }
  };

  const handleInspect = async (resumeId: string) => {
    setLoadingDetail(true);
    setInspectModalOpen(true);
    setInspectCandidate(null);
    setErrorMsg(null);
    try {
      const detail = await getResumeById(resumeId);
      setInspectCandidate(detail);
    } catch (err: any) {
      setErrorMsg(err.detail || 'Failed to load candidate details.');
      setInspectModalOpen(false);
    } finally {
      setLoadingDetail(false);
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
    const candStatus = (c.status || 'pending').toLowerCase();
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'pending' && (candStatus === 'pending' || candStatus === 'list_candidates')) ||
      (statusFilter === 'shortlist' && (candStatus === 'shortlist' || candStatus === 'shortlisted')) ||
      (statusFilter === 'reject' && (candStatus === 'reject' || candStatus === 'rejected'));
    return matchesSearch && matchesCat && matchesStatus;
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

        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white text-slate-700"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Domains' : cat}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white text-slate-700"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending Review</option>
            <option value="shortlist">Shortlisted</option>
            <option value="reject">Declined</option>
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
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Uploaded</th>
                  <th className="px-6 py-3.5 text-right">Recruiter Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((cand) => {
                  const s = (cand.status || 'pending').toLowerCase();
                  const isShortlisted = s === 'shortlist' || s === 'shortlisted';
                  const isRejected = s === 'reject' || s === 'rejected';

                  return (
                    <tr key={cand.resume_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2.5">
                          <FileText className="h-4 w-4 text-indigo-600 flex-shrink-0" />
                          <div>
                            <span className="font-semibold text-slate-900 block truncate max-w-[200px]">
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

                      <td className="px-6 py-4">
                        {isShortlisted ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle className="h-3 w-3" />
                            <span>Shortlisted</span>
                          </span>
                        ) : isRejected ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            <XCircle className="h-3 w-3" />
                            <span>Declined</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            <Clock className="h-3 w-3" />
                            <span>Pending</span>
                          </span>
                        )}
                      </td>

                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(cand.uploaded_at).toLocaleDateString()}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleInspect(cand.resume_id)}
                            className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                            title="Inspect candidate extracted skills and profile"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            <span>Inspect</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleAction(cand.resume_id, 'shortlist')}
                            disabled={isShortlisted}
                            className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors disabled:opacity-50"
                          >
                            <CheckCircle className="h-3.5 w-3.5" />
                            <span>{isShortlisted ? 'Shortlisted' : 'Shortlist'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => handleAction(cand.resume_id, 'reject')}
                            disabled={isRejected}
                            className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            <span>{isRejected ? 'Declined' : 'Decline'}</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Candidate Profile Inspection Modal */}
      {inspectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 shadow-xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-base">Candidate Profile Inspection</h3>
              </div>
              <button
                type="button"
                onClick={() => setInspectModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {loadingDetail ? (
              <div className="py-12 text-center text-sm text-slate-400">Loading parsed candidate profile...</div>
            ) : inspectCandidate ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-400 block font-medium">Document</span>
                    <span className="font-semibold text-slate-900 mt-0.5 block truncate">
                      {inspectCandidate.original_filename}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-400 block font-medium">Predicted Career Family</span>
                    <span className="font-semibold text-indigo-700 mt-0.5 block">
                      {inspectCandidate.predicted_category} ({(inspectCandidate.category_confidence * 100).toFixed(1)}%)
                    </span>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Extracted Technical Skills ({inspectCandidate.extracted_skills.length})</span>
                  </h4>
                  {inspectCandidate.extracted_skills.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No recognized lexicon skills detected.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {inspectCandidate.extracted_skills.map((skill) => (
                        <SkillPill key={skill} name={skill} />
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    PII-Sanitized Text Preview
                  </h4>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-700 max-h-48 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                    {inspectCandidate.extracted_text_preview || 'No preview available.'}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      handleAction(inspectCandidate.id, 'shortlist');
                      setInspectModalOpen(false);
                    }}
                    className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                  >
                    <CheckCircle className="h-3.5 w-3.5" />
                    <span>Shortlist Candidate</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      handleAction(inspectCandidate.id, 'reject');
                      setInspectModalOpen(false);
                    }}
                    className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors"
                  >
                    <XCircle className="h-3.5 w-3.5" />
                    <span>Decline Candidate</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setInspectModalOpen(false)}
                    className="text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
