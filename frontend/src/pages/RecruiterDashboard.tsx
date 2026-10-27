import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  History,
  ShieldCheck,
  ArrowRight,
  Clock,
  FileText,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { StatCard } from '../components/common/StatCard';
import { getRecruiterCandidates, getRecruiterActions } from '../api';
import type { CandidateSummary, RecruiterActionOut } from '../api/types';
import { Alert } from '../components/common/Alert';

export const RecruiterDashboard: React.FC = () => {
  const { isRecruiter } = useAuth();
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [actions, setActions] = useState<RecruiterActionOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isRecruiter) return;

    Promise.all([
      getRecruiterCandidates().catch((err) => {
        setErrorMsg(err.detail || 'Failed to load candidates.');
        return [];
      }),
      getRecruiterActions().catch(() => []),
    ])
      .then(([c, a]) => {
        setCandidates(c);
        setActions(a);
      })
      .finally(() => setLoading(false));
  }, [isRecruiter]);

  if (!isRecruiter) {
    return (
      <div className="py-12 max-w-xl mx-auto">
        <Alert type="error" title="Access Denied">
          This portal is restricted to authenticated Recruiter and Administrator accounts.
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Recruiter Command Center
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Monitor candidate submissions, audit recruiter workflow actions, and evaluate role
            alignment.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/recruiter/candidates"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <Users className="h-4 w-4" />
            <span>Manage Candidates</span>
          </Link>
        </div>
      </div>

      {errorMsg && (
        <Alert type="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <StatCard
          title="Total Ingested Candidates"
          value={candidates.length}
          subtitle="Processed & classified resumes"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          title="Audit Trail Entries"
          value={actions.length}
          subtitle="Compliance recorded actions"
          icon={<History className="h-5 w-5" />}
        />
        <StatCard
          title="Access Control"
          value="RBAC Enforced"
          subtitle="Protected candidate records"
          icon={<ShieldCheck className="h-5 w-5" />}
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Ingested Candidates */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base">Recent Candidate Submissions</h3>
            <Link
              to="/recruiter/candidates"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-sm text-slate-400">Loading candidate records...</div>
          ) : candidates.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500">
              No resumes uploaded yet. Upload a resume via Resume Analyzer to test the flow.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {candidates.slice(0, 5).map((cand) => (
                <div key={cand.resume_id} className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900 truncate max-w-[200px]">
                        {cand.original_filename}
                      </p>
                      <p className="text-xs text-slate-400">
                        {new Date(cand.uploaded_at).toLocaleDateString()} • {(cand.file_size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 block">
                      {cand.predicted_category}
                    </span>
                    <span className="text-[11px] font-medium capitalize mt-0.5 block text-slate-500">
                      {cand.status === 'shortlist' || cand.status === 'shortlisted' ? (
                        <span className="text-emerald-600 font-semibold">Shortlisted</span>
                      ) : cand.status === 'reject' || cand.status === 'rejected' ? (
                        <span className="text-rose-600 font-semibold">Declined</span>
                      ) : (
                        <span>Pending Review</span>
                      )}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Audit Actions Log */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-base">Compliance Audit Trail</h3>
            <span className="text-xs font-mono text-slate-400">recruiter_actions</span>
          </div>

          {loading ? (
            <div className="py-8 text-center text-sm text-slate-400">Loading audit trail...</div>
          ) : actions.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500">
              No audit actions logged yet. Querying candidates logs events automatically.
            </div>
          ) : (
            <div className="space-y-3">
              {actions.slice(0, 5).map((act) => (
                <div
                  key={act.id}
                  className="p-3 rounded-lg bg-slate-50 border border-slate-200/60 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-semibold text-slate-800 uppercase tracking-wider text-[11px] block">
                      {act.action_type}
                    </span>
                    <span className="text-slate-500 text-[11px]">
                      Target: {act.target_entity_type} ({act.target_entity_id.slice(0, 12)}...)
                    </span>
                  </div>
                  <div className="text-right text-slate-400 text-[11px] flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{new Date(act.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
