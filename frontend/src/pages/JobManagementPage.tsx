import React, { useEffect, useState } from 'react';
import {
  Lock,
  Building,
  MapPin,
} from 'lucide-react';
import { getJobs } from '../api';
import type { JobRecommendItem } from '../api/types';
import { Alert } from '../components/common/Alert';

export const JobManagementPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobRecommendItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    getJobs({ limit: 50 })
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Job Repertoire Management
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Inspect active postings normalized from repository job datasets.
          </p>
        </div>

        {/* Disabled Action Button with Explicit Backend Disclosure */}
        <div className="relative group">
          <button
            type="button"
            disabled
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-200 text-slate-500 rounded-lg text-sm font-semibold cursor-not-allowed border border-slate-300"
          >
            <Lock className="h-4 w-4 text-slate-400" />
            <span>Post New Job (Unavailable)</span>
          </button>
          <div className="hidden group-hover:block absolute right-0 top-full mt-1 w-64 p-2 bg-slate-800 text-white text-xs rounded shadow-lg z-20">
            POST /api/v1/jobs is not implemented in Backend v1. Postings are ingested via dataset
            pipelines.
          </div>
        </div>
      </div>

      {/* Backend Limitation Disclosure Banner */}
      <Alert type="info" title="Backend Architecture Notice">
        <span>
          Backend v1 supports read and filter operations on job records populated from normalized
          repository datasets (<code>data/processed/jobs.csv</code>). Direct creation, editing, and
          deletion endpoints are unsupported by the current backend contract and are disabled to
          prevent fabricated state.
        </span>
      </Alert>

      {/* Jobs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-900">
            Verified Job Records ({jobs.length})
          </span>
          <span className="text-xs text-slate-400 font-mono">GET /api/v1/jobs</span>
        </div>

        {loading ? (
          <div className="py-16 text-center text-sm text-slate-400">Loading job postings...</div>
        ) : jobs.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-500">No job records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-slate-500 font-semibold text-xs uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3.5">Job ID & Role</th>
                  <th className="px-6 py-3.5">Company & Location</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Experience & Salary</th>
                  <th className="px-6 py-3.5 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.map((job) => (
                  <tr key={job.job_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4">
                      <span className="font-mono text-xs text-slate-400 block">{job.job_id}</span>
                      <span className="font-semibold text-slate-900 text-sm">{job.title}</span>
                    </td>

                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1 font-medium text-slate-800">
                        <Building className="h-3.5 w-3.5 text-slate-400" />
                        {job.company}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-slate-400 mt-0.5">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" />
                        {job.location}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {job.category || 'General'}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      <div>Exp: {job.experience || 'Not specified'}</div>
                      <div>{job.salary || 'Salary undisclosed'}</div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Active Dataset
                      </span>
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
