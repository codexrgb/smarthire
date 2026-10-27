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
  let colorClasses = 'bg-slate-100 text-slate-800 border-slate-200';
  let barColor = 'bg-slate-500';

  if (normalizedScore >= 75) {
    colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-200';
    barColor = 'bg-emerald-600';
  } else if (normalizedScore >= 50) {
    colorClasses = 'bg-blue-50 text-blue-800 border-blue-200';
    barColor = 'bg-blue-600';
  } else if (normalizedScore >= 30) {
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-200';
    barColor = 'bg-amber-600';
  } else {
    colorClasses = 'bg-rose-50 text-rose-800 border-rose-200';
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
        <span className="text-slate-600 text-xs font-normal">Compatibility Index</span>
      </div>

      <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-1.5 rounded-full ${barColor} transition-all duration-300`}
          style={{ width: `${normalizedScore}%` }}
        />
      </div>

      {showExplanation && (
        <p className="flex items-start gap-1 text-[11px] text-slate-500 mt-0.5 leading-tight">
          <Info className="h-3 w-3 flex-shrink-0 mt-0.5 text-slate-400" />
          <span>
            Deterministic heuristic index: 50% Text Similarity + 30% Skill Overlap + 20%
            Experience. Not a calibrated hiring probability.
          </span>
        </p>
      )}
    </div>
  );
};
