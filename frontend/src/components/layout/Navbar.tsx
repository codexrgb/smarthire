import React from 'react';
import { Menu, Activity, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';

interface NavbarProps {
  onToggleSidebar: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
          className="lg:hidden p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">Platform:</span>
          <span>TF-IDF + Cosine Recommender</span>
          <span className="text-slate-300">•</span>
          <span>Classical NLP</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Academic / ML Status Badge */}
        <Link
          to="/analytics"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors border border-slate-200"
          title="Inspect ML pipelines & provenance"
        >
          <Activity className="h-3.5 w-3.5 text-indigo-600" />
          <span className="hidden md:inline">ML Status</span>
        </Link>

        {/* User Pill */}
        {user ? (
          <Link
            to="/settings"
            className="flex items-center gap-2 pl-2 pr-3 py-1 rounded-full border border-slate-200 hover:border-slate-300 bg-slate-50 transition-colors"
          >
            <div className="h-6 w-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <span className="text-xs font-medium text-slate-700 hidden sm:inline">
              {user.full_name}
            </span>
            <span className="text-[10px] uppercase font-semibold text-slate-400">
              ({user.role})
            </span>
          </Link>
        ) : (
          <Link
            to="/auth"
            className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
          >
            <UserIcon className="h-3.5 w-3.5" />
            <span>Sign In</span>
          </Link>
        )}
      </div>
    </header>
  );
};
