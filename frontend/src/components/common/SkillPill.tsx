import React from 'react';
import { Check, X } from 'lucide-react';

interface SkillPillProps {
  name: string;
  variant?: 'matched' | 'missing' | 'neutral';
  size?: 'sm' | 'md';
}

export const SkillPill: React.FC<SkillPillProps> = ({
  name,
  variant = 'neutral',
  size = 'md',
}) => {
  const baseClasses = 'inline-flex items-center gap-1 font-medium rounded-md border transition-colors';

  const variantClasses = {
    matched:
      'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
    missing:
      'bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-800',
    neutral:
      'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700',
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs sm:text-sm px-2.5 py-1',
  };

  return (
    <span className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}>
      {variant === 'matched' && <Check className="h-3 w-3 text-emerald-600" aria-hidden="true" />}
      {variant === 'missing' && <X className="h-3 w-3 text-rose-600" aria-hidden="true" />}
      <span>{name}</span>
    </span>
  );
};
