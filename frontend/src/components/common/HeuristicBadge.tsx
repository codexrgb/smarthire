import React from 'react';
import { Info } from 'lucide-react';

interface HeuristicBadgeProps {
  score: number; // 0 - 100
  showExplanation?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const HeuristicBadge: React.FC<HeuristicBadgeProps> = ({
  score,
  showExplanation = false,
  size = 'md',
}) => {
  const normalizedScore = Math.max(0, Math.min(100, Math.round(score)));

  // Color classes based on score
  let colorClasses =
    'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700';
  let barColor = 'bg-slate-500';

  if (normalizedScore >= 75) {
    colorClasses =
      'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
    barColor = 'bg-emerald-600';
  } else if (normalizedScore >= 50) {
    colorClasses =
      'bg-blue-50 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800';
    barColor = 'bg-blue-600';
  } else if (normalizedScore >= 30) {
    colorClasses =
      'bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800';
    barColor = 'bg-amber-600';
  } else {
    colorClasses =
      'bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800';
    barColor = 'bg-rose-600';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3.5 py-1.5 font-semibold',
  };

  return (
    <div className="inline-flex flex-col gap-1.5">
      <div
        className={`inline-flex items-center gap-2 rounded-lg border font-medium ${colorClasses} ${sizeClasses[size]}`}
      >
        <span className="font-bold">{normalizedScore}%</span>
        <span className="text-slate-600 dark:text-slate-400 text-xs font-normal">Compatibility Index</span>
      </div>

      <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-1.5 rounded-full ${barColor} transition-all duration-300`}
          style={{ width: `${normalizedScore}%` }}
        />
      </div>

      {showExplanation && (
        <p className="flex items-start gap-1 text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">
          <Info className="h-3 w-3 flex-shrink-0 mt-0.5 text-slate-400 dark:text-slate-500" />
          <span>
            Deterministic heuristic index: 50% Text Similarity + 30% Skill Overlap + 20%
            Experience. Not a calibrated hiring probability.
          </span>
        </p>
      )}
    </div>
  );
};
