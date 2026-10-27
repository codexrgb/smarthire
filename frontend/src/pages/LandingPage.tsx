import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Briefcase,
  GitCompare,
  TrendingUp,
  Cpu,
  ArrowRight,
} from 'lucide-react';
import { getHealth, getModelsStatus } from '../api';
import type { HealthResponse, ModelStatusResponse } from '../api/types';
import { ProvenanceBanner } from '../components/common/ProvenanceBanner';

export const LandingPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelsStatus, setModelsStatus] = useState<ModelStatusResponse | null>(null);

  useEffect(() => {
    Promise.all([getHealth().catch(() => null), getModelsStatus().catch(() => null)]).then(
      ([h, m]) => {
        setHealth(h);
        setModelsStatus(m);
      }
    );
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <ProvenanceBanner />

      {/* Top Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-xs">
              SH
            </div>
            <div>
              <span className="font-bold text-slate-900 text-base">SmartHire 2.0</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-mono text-slate-400">
                Classical NLP
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/jobs"
              className="text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-1.5"
            >
              Explore Jobs
            </Link>
            <Link
              to="/auth"
              className="text-xs sm:text-sm font-semibold px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors shadow-xs"
            >
              Sign In / Register
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200 mb-6">
            <Cpu className="h-3.5 w-3.5" />
            <span>Deterministic Machine Learning • Zero Generative Hallucination</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Transparent Resume Intelligence & Career Alignment
          </h1>

          <p className="mt-5 text-lg text-slate-600 leading-relaxed">
            SmartHire 2.0 automates resume categorization, local job matching, and skill-gap
            analysis using validated classical NLP: TF-IDF vectorization, Cosine Similarity, and
            transparent multi-factor heuristic scoring.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/resumes/analyze"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-colors shadow-sm"
            >
              <FileText className="h-4 w-4" />
              <span>Analyze Your Resume</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
            <Link
              to="/jobs"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-white border border-slate-300 text-slate-700 font-medium hover:bg-slate-50 transition-colors shadow-xs"
            >
              <Briefcase className="h-4 w-4" />
              <span>Browse Job Listings</span>
            </Link>
          </div>
        </div>

        {/* Live Backend Diagnostic Pill */}
        <div className="mt-12 p-4 rounded-xl border border-slate-200 bg-white shadow-xs max-w-2xl">
          <div className="flex items-center justify-between text-xs font-medium text-slate-500 mb-2">
            <span>LIVE REST BACKEND STATUS</span>
            <span className="flex items-center gap-1.5">
              <span
                className={`h-2 w-2 rounded-full ${
                  health?.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                }`}
              />
              {health?.status === 'healthy' ? 'Connected' : 'Offline / Checking'}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <p className="text-slate-400">API Version</p>
              <p className="font-bold text-slate-800">{health?.version || '2.0.0'}</p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <p className="text-slate-400">Database</p>
              <p className="font-bold text-slate-800">
                {health?.database_connected ? 'Connected' : 'SQLite fallback'}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <p className="text-slate-400">Classifier</p>
              <p className="font-bold text-slate-800">
                {modelsStatus?.best_classifier || 'LogisticRegression'}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <p className="text-slate-400">Provenance</p>
              <p className="font-bold text-slate-800">
                {modelsStatus?.dataset_provenance?.overall_status || 'Assessing'}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Core Architectural Modules */}
      <section className="py-12 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Scientific Pipeline Modules
          </h2>
          <p className="text-sm text-slate-500 mt-1 max-w-2xl">
            Every feature is backed by open, reproducible machine learning formulas without black-box
            APIs.
          </p>

          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="h-10 w-10 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center mb-4">
                <FileText className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-slate-900 text-base">Resume Categorization</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Categorizes candidate resumes into 25 job families via TF-IDF vectorization
                (10,000 unigram/bigram features) and calibrated multiclass Logistic Regression.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="h-10 w-10 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center mb-4">
                <GitCompare className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-slate-900 text-base">
                Multi-Factor Compatibility
              </h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Computes an interpretable heuristic fit score from 50% TF-IDF cosine similarity,
                30% skill overlap, and 20% experience matching. Explicitly marked as a non-probability
                index.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="h-10 w-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
                <TrendingUp className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-slate-900 text-base">Skill-Gap Detection</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                Extracts technical skills with word-boundary isolation against an authoritative
                technical skill lexicon, isolating candidate strengths and missing requirements.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-8 px-4 text-center text-xs text-slate-500">
        <p>
          SmartHire 2.0 • Classical Machine Learning Portal • Built with React, TypeScript, FastAPI,
          and PostgreSQL.
        </p>
      </footer>
    </div>
  );
};
