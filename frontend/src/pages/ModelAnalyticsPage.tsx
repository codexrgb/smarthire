import React, { useEffect, useState } from 'react';
import {
  Cpu,
  CheckCircle2,
  XCircle,
  Info,
  TrendingUp,
  Layers,
  Sparkles,
} from 'lucide-react';
import { getModelsStatus } from '../api';
import type { ModelStatusResponse } from '../api/types';
import { StatCard } from '../components/common/StatCard';
import { Alert } from '../components/common/Alert';

export const ModelAnalyticsPage: React.FC = () => {
  const [status, setStatus] = useState<ModelStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    getModelsStatus()
      .then(setStatus)
      .catch((err) => setErrorMsg(err.detail || 'Failed to load model diagnostics.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Model Analytics & Provenance Diagnostics
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Transparent inspection of classical machine learning artifacts, vectorizers, and dataset
          authenticity markers.
        </p>
      </div>

      {errorMsg && (
        <Alert type="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Dataset Provenance Diagnostic */}
      {status?.demo_warning_active && (
        <Alert type="warning" title="Academic Integrity Warning: Synthetic Dataset In Use">
          <span>
            {status.dataset_provenance?.banner_message ||
              'Synthetic data generation signatures detected. Classification accuracy of 100% reflects template memorization rather than real-world generalizability.'}
          </span>
        </Alert>
      )}

      {/* High Level Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <StatCard
          title="Classifier Architecture"
          value={status?.best_classifier || 'Logistic Regression'}
          subtitle="Multiclass with balanced class weights"
          icon={<Cpu className="h-5 w-5" />}
        />
        <StatCard
          title="Vectorization Space"
          value="TF-IDF"
          subtitle="10,000 unigram/bigram features"
          icon={<Layers className="h-5 w-5" />}
        />
        <StatCard
          title="Clustering Algorithm"
          value="K-Means (K=5)"
          subtitle="Unsupervised job family grouping"
          icon={<TrendingUp className="h-5 w-5" />}
        />
      </div>

      {/* Saved Joblib Models Inspection Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <h3 className="font-bold text-slate-900 text-base mb-1">
          Production Model Artifacts (Disk Verification)
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Inspecting serialized <code>models/*.pkl</code> artifacts on backend storage
        </p>

        {loading ? (
          <div className="py-8 text-center text-sm text-slate-400">Verifying model files...</div>
        ) : !status?.models_loaded ? (
          <div className="py-8 text-center text-sm text-slate-400">Unable to inspect models.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(status.models_loaded).map(([name, isLoaded]) => (
              <div
                key={name}
                className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 flex items-center justify-between"
              >
                <div>
                  <span className="font-mono text-xs font-semibold text-slate-800 block">
                    {name}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {name.includes('vectorizer')
                      ? 'Feature Extractor'
                      : name.includes('clustering')
                      ? 'K-Means Model'
                      : name.includes('pca')
                      ? '2D Projection'
                      : 'Classifier'}
                  </span>
                </div>
                {isLoaded ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />
                ) : (
                  <XCircle className="h-5 w-5 text-rose-500 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Clustering & Feature Engineering Disclosures */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <h4 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <Info className="h-4 w-4 text-indigo-600" />
            <span>Clustering Silhouette Trade-Off</span>
          </h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            In high-dimensional sparse TF-IDF spaces, Euclidean distances concentrate near
            orthogonal boundaries. Higher silhouette scores at K=10 (0.1108) vs K=5 (0.0528) arise
            from micro-clusters on the unit hypersphere rather than superior semantic coherence. K=5
            is maintained for operational interpretability.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <h4 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-600" />
            <span>Word-Boundary Skill Extraction</span>
          </h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            Skills are extracted strictly using word-boundary regular expressions (<code>\b(AI)\b</code>)
            against an extendable master technical skill dictionary. This explicitly prevents false
            positive collisions (e.g., matching 'AI' in 'email' or 'claim').
          </p>
        </div>
      </div>
    </div>
  );
};
