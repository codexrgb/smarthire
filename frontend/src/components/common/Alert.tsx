import React, { type ReactNode } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: ReactNode;
  onClose?: () => void;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  onClose,
}) => {
  const styles = {
    info: 'bg-blue-50 border-blue-200 text-blue-900',
    success: 'bg-emerald-50 border-emerald-200 text-emerald-900',
    warning: 'bg-amber-50 border-amber-200 text-amber-900',
    error: 'bg-rose-50 border-rose-200 text-rose-900',
  };

  const icons = {
    info: <Info className="h-5 w-5 text-blue-600 flex-shrink-0" />,
    success: <CheckCircle className="h-5 w-5 text-emerald-600 flex-shrink-0" />,
    warning: <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />,
    error: <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />,
  };

  return (
    <div
      role="alert"
      className={`rounded-lg border p-4 ${styles[type]} flex items-start gap-3`}
    >
      {icons[type]}
      <div className="flex-1 text-sm">
        {title && <h5 className="font-semibold mb-1">{title}</h5>}
        <div>{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          type="button"
          aria-label="Close alert"
          className="text-slate-400 hover:text-slate-600 rounded p-1"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};
