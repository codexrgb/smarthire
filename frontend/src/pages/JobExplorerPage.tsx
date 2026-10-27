import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  MapPin,
  Building,
  Briefcase,
  DollarSign,
  Clock,
  Filter,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { getJobs } from '../api';
import type { JobRecommendItem } from '../api/types';
import { SkillPill } from '../components/common/SkillPill';

export const JobExplorerPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobRecommendItem[]>([]);
  const [titleFilter, setTitleFilter] = useState<string>('');
  const [locationFilter, setLocationFilter] = useState<string>('');
  const [limit, setLimit] = useState<number>(20);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const navigate = useNavigate();

  const fetchJobs = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getJobs({
        title: titleFilter.trim() || undefined,
        location: locationFilter.trim() || undefined,
        limit,
      });
      setJobs(data);
    } catch (err) {
      setErrorMsg('Failed to load jobs from the database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [limit]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJobs();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Job Explorer
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Browse verified postings normalized from the SmartHire job corpus.
        </p>
      </div>

      {/* Search and Filters Card */}
      <form
        onSubmit={handleSearchSubmit}
        className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs grid grid-cols-1 sm:grid-cols-3 gap-3"
      >
        <div className="relative rounded-md shadow-2xs">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="h-4 w-4" />
          </div>
          <input
            type="text"
            placeholder="Search by job title, role..."
            value={titleFilter}
            onChange={(e) => setTitleFilter(e.target.value)}
            className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
          />
        </div>

        <div className="relative rounded-md shadow-2xs">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <MapPin className="h-4 w-4" />
          </div>
          <input
            type="text"
            placeholder="Location filter (e.g. Remote, City)..."
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            type="submit"
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <Filter className="h-4 w-4" />
            <span>Filter Postings</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setTitleFilter('');
              setLocationFilter('');
              setLimit(20);
              getJobs({ limit: 20 }).then(setJobs);
            }}
            className="px-3 py-2 border border-slate-300 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
          >
            Reset
          </button>
        </div>
      </form>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>
          Showing <strong>{jobs.length}</strong> active job postings
        </span>
        <div className="flex items-center gap-2">
          <span>Page limit:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="border border-slate-300 rounded px-2 py-1 text-xs bg-white text-slate-700"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* Jobs Listing */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">
          Loading postings from database...
        </div>
      ) : errorMsg ? (
        <div className="py-16 text-center text-rose-500 text-sm">{errorMsg}</div>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <Briefcase className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-900">No matching jobs found</h3>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your title or location filter keywords.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {jobs.map((job) => {
            const skillList = job.skills
              ? job.skills
                  .split(',')
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .slice(0, 6)
              : [];

            return (
              <div
                key={job.job_id}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {job.category || 'General'}
                    </span>
                    <span className="text-xs font-mono text-slate-400">ID: {job.job_id}</span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900">{job.title}</h3>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1 font-medium text-slate-700">
                      <Building className="h-3.5 w-3.5 text-slate-400" />
                      {job.company}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" />
                      {job.location}
                    </span>
                    {job.salary && job.salary !== 'N/A' && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3.5 w-3.5 text-slate-400" />
                        {job.salary}
                      </span>
                    )}
                    {job.experience && job.experience !== 'N/A' && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-slate-400" />
                        {job.experience}
                      </span>
                    )}
                  </div>

                  {skillList.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {skillList.map((skill) => (
                        <SkillPill key={skill} name={skill} size="sm" />
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center md:flex-col justify-end gap-2 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/matching?job_title=${encodeURIComponent(job.title)}&job_text=${encodeURIComponent(
                          job.skills || job.title
                        )}`
                      )
                    }
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition-colors shadow-2xs"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Calculate Compatibility</span>
                    <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
