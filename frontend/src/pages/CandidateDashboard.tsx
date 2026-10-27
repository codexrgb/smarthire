import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Briefcase,
  GitCompare,
  TrendingUp,
  ArrowRight,
  Sparkles,
  Building,
  MapPin,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { StatCard } from '../components/common/StatCard';
import { getJobs, getMyResumes, deleteResume } from '../api';
import type { JobRecommendItem, ResumeSummaryOut } from '../api/types';
import { Alert } from '../components/common/Alert';
import { formatFirstName } from '../utils/name';

export const CandidateDashboard: React.FC = () => {
  const { user } = useAuth();
  const [recentJobs, setRecentJobs] = useState<JobRecommendItem[]>([]);
  const [myResumes, setMyResumes] = useState<ResumeSummaryOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingResumes, setLoadingResumes] = useState<boolean>(true);
  const [resumeFeedback, setResumeFeedback] = useState<string | null>(null);
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchResumes = async () => {
    setLoadingResumes(true);
    setResumeError(null);
    try {
      const data = await getMyResumes();
      setMyResumes(data);
    } catch {
      setMyResumes([]);
    } finally {
      setLoadingResumes(false);
    }
  };

  useEffect(() => {
    fetchResumes();
    getJobs({ limit: 4 })
      .then((jobs) => setRecentJobs(jobs))
      .catch(() => setRecentJobs([]))
      .finally(() => setLoading(false));
  }, []);

  const handleDeleteResume = async (resumeId: string) => {
    if (!window.confirm('Are you sure you want to delete this resume? This cannot be undone.')) {
      return;
    }
    setDeletingId(resumeId);
    setResumeError(null);
    try {
      await deleteResume(resumeId);
      setMyResumes((prev) => prev.filter((r) => r.id !== resumeId));
      setResumeFeedback('Resume document deleted successfully.');
      setTimeout(() => setResumeFeedback(null), 4000);
    } catch (err: any) {
      setResumeError(err.detail || 'Failed to delete resume.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Hero Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 sm:p-8 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 mb-3">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Candidate Portal Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {user?.is_first_login
              ? `Welcome, ${formatFirstName(user?.full_name, 'Candidate')}!`
              : `Welcome back, ${formatFirstName(user?.full_name, 'Candidate')}!`}
          </h1>
          <p className="mt-2 text-sm text-slate-300 max-w-xl leading-relaxed">
            {user?.is_first_login
              ? 'Welcome to SmartHire. Upload your resume to discover relevant jobs and analyze your skills.'
              : 'Upload your resume to extract validated technical skills, classify into industry categories, and discover jobs ranked with TF-IDF cosine similarity.'}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            to="/resumes/analyze"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm transition-colors shadow-xs"
          >
            <FileText className="h-4 w-4" />
            <span>Analyze Resume</span>
          </Link>
          <Link
            to="/jobs"
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-white/10 hover:bg-white/20 font-semibold text-sm transition-colors border border-white/20"
          >
            <Briefcase className="h-4 w-4" />
            <span>Explore Jobs</span>
          </Link>
        </div>
      </div>

      {/* Key Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Classical Pipeline"
          value="TF-IDF + Cosine"
          subtitle="15,000 vocabulary unigram/bigram"
          icon={<Sparkles className="h-5 w-5" />}
        />
        <StatCard
          title="Job Categories"
          value="25 Families"
          subtitle="Logistic Regression classifier"
          icon={<Briefcase className="h-5 w-5" />}
        />
        <StatCard
          title="Skill Lexicon"
          value="Regex Isolated"
          subtitle="Word boundary protection"
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <StatCard
          title="Matching Formula"
          value="3-Factor Heuristic"
          subtitle="Non-probability index"
          icon={<GitCompare className="h-5 w-5" />}
        />
      </div>

      {resumeFeedback && (
        <Alert type="success" onClose={() => setResumeFeedback(null)}>
          {resumeFeedback}
        </Alert>
      )}

      {resumeError && (
        <Alert type="error" onClose={() => setResumeError(null)}>
          {resumeError}
        </Alert>
      )}

      {/* Uploaded Resumes Portfolio */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs transition-colors">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Your Uploaded Resumes</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Manage your parsed resumes, domain classification, and trigger matching
            </p>
          </div>
          <Link
            to="/resumes/analyze"
            className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors flex items-center gap-1 shadow-2xs"
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Upload New Resume</span>
          </Link>
        </div>

        {loadingResumes ? (
          <div className="py-8 text-center text-sm text-slate-400 dark:text-slate-500">Loading your resumes...</div>
        ) : myResumes.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg p-6">
            <p className="font-medium text-slate-700 dark:text-slate-300">No resumes uploaded yet</p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
              Upload your resume to extract validated technical skills, classify career families, and view personalized matches.
            </p>
            <Link
              to="/resumes/analyze"
              className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-colors"
            >
              <span>Upload Your First Resume</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {myResumes.map((res) => (
              <div key={res.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white truncate max-w-xs">{res.original_filename}</h4>
                    <p className="text-xs text-slate-400 dark:text-slate-500">
                      Uploaded {new Date(res.uploaded_at).toLocaleDateString()} • {(res.file_size_bytes / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-wrap sm:flex-nowrap">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                    {res.predicted_category} ({(res.category_confidence * 100).toFixed(0)}%)
                  </span>

                  <Link
                    to={`/matching?resume_id=${res.id}`}
                    className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-1"
                  >
                    <span>Match</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>

                  <button
                    type="button"
                    onClick={() => handleDeleteResume(res.id)}
                    disabled={deletingId === res.id}
                    className="text-xs font-semibold px-2.5 py-1.5 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors disabled:opacity-50 flex items-center gap-1"
                    title="Delete resume"
                    aria-label={`Delete ${res.original_filename}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span className="sr-only">Delete {res.original_filename}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Action Shortcuts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/resumes/analyze"
          className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-md transition-all group"
        >
          <div className="h-10 w-10 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <FileText className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-slate-900 dark:text-white text-base">Resume Analyzer</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Parse your resume, extract technical skills, and predict job category.
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 mt-4">
            Get started <ArrowRight className="h-3 w-3" />
          </span>
        </Link>

        <Link
          to="/matching"
          className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-md transition-all group"
        >
          <div className="h-10 w-10 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <GitCompare className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-slate-900 dark:text-white text-base">Job Match Details</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Compare candidate text directly with any job description for 3-part scoring.
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-purple-600 dark:text-purple-400 mt-4">
            Test compatibility <ArrowRight className="h-3 w-3" />
          </span>
        </Link>

        <Link
          to="/skill-gap"
          className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-md transition-all group"
        >
          <div className="h-10 w-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <TrendingUp className="h-5 w-5" />
          </div>
          <h3 className="font-semibold text-slate-900 dark:text-white text-base">Skill Gap Analysis</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Discover matched competencies and missing skills to guide career development.
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-4">
            Analyze gaps <ArrowRight className="h-3 w-3" />
          </span>
        </Link>
      </div>

      {/* Featured Jobs from Real Dataset */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs transition-colors">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Featured Job Openings</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Directly loaded from the normalized SmartHire dataset
            </p>
          </div>
          <Link
            to="/jobs"
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 flex items-center gap-1"
          >
            <span>View all jobs</span>
            <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        {loading ? (
          <div className="py-8 text-center text-sm text-slate-400 dark:text-slate-500">Loading dataset jobs...</div>
        ) : recentJobs.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            No job records found. Make sure processed data exists in the backend.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recentJobs.map((job) => (
              <div
                key={job.job_id}
                className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-slate-50 dark:hover:bg-slate-800/70 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
                    <span className="font-medium text-indigo-600 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-100 dark:border-indigo-800">
                      {job.category || 'General'}
                    </span>
                    <span className="font-mono">{job.job_id}</span>
                  </div>
                  <h4 className="font-semibold text-slate-900 dark:text-white text-sm">{job.title}</h4>
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500 dark:text-slate-400">
                    <span className="flex items-center gap-1">
                      <Building className="h-3 w-3" />
                      {job.company}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {job.location}
                    </span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between">
                  <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                    Exp: {job.experience || 'Not specified'}
                  </span>
                  <Link
                    to={`/matching?job_title=${encodeURIComponent(job.title)}&job_text=${encodeURIComponent(job.skills || '')}`}
                    className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 flex items-center gap-1"
                  >
                    Match <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
