import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import type { DatasetProvenance } from '../../api/types';
import { getModelsStatus } from '../../api';

interface ProvenanceBannerProps {
  provenance?: DatasetProvenance;
}

export const ProvenanceBanner: React.FC<ProvenanceBannerProps> = ({ provenance: propProv }) => {
  const [provenance, setProvenance] = useState<DatasetProvenance | null>(propProv || null);
  const [loading, setLoading] = useState<boolean>(!propProv);

  useEffect(() => {
    if (propProv) {
      setProvenance(propProv);
      return;
    }

    let isMounted = true;
    getModelsStatus()
      .then((res) => {
        if (isMounted) setProvenance(res.dataset_provenance);
      })
      .catch(() => {
        // Fallback or offline
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [propProv]);

  if (loading || !provenance) {
    return null;
  }

  if (provenance.overall_status === 'demo_synthetic' || provenance.is_demo_mode) {
    return (
      <aside
        aria-label="Dataset Provenance Alert"
        className="w-full bg-amber-500/10 dark:bg-amber-950/30 border-b border-amber-500/30 dark:border-amber-800/40 text-amber-900 dark:text-amber-200 px-4 py-2.5 sm:px-6 transition-colors"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-2 text-xs sm:text-sm font-medium">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" aria-hidden="true" />
            <span>
              <strong className="font-semibold text-amber-950 dark:text-amber-100">DEMO MODE ACTIVE:</strong> Synthetic
              template data detected. Results and metrics reflect template memorization and cannot
              establish real-world generalization.
            </span>
          </div>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-200/80 dark:bg-amber-900/50 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-700">
            Synthetic Provenance
          </span>
        </div>
      </aside>
    );
  }

  if (provenance.overall_status === 'unknown_unverified') {
    return (
      <aside
        aria-label="Dataset Provenance Alert"
        className="w-full bg-blue-500/10 dark:bg-blue-950/30 border-b border-blue-500/30 dark:border-blue-800/40 text-blue-900 dark:text-blue-200 px-4 py-2 sm:px-6 transition-colors"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <span>
              <strong>UNVERIFIED MODE:</strong> Data lacks cryptographic provenance manifest.
            </span>
          </div>
          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-200 dark:bg-blue-900/50 text-blue-900 dark:text-blue-200">
            Unverified
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside
      aria-label="Dataset Provenance Alert"
      className="w-full bg-emerald-500/10 dark:bg-emerald-950/30 border-b border-emerald-500/30 dark:border-emerald-800/40 text-emerald-900 dark:text-emerald-200 px-4 py-2 sm:px-6 transition-colors"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between text-xs sm:text-sm">
        <div className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
          <span>
            <strong>AUTHENTIC MODE:</strong> Cryptographic checksum verified against data manifest.
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-200 dark:bg-emerald-900/50 text-emerald-900 dark:text-emerald-200">
          Verified Authentic
        </span>
      </div>
    </aside>
  );
};
