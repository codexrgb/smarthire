import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  FileText,
  Briefcase,
  GitCompare,
  TrendingUp,
  BarChart2,
  Users,
  Settings,
  LayoutDashboard,
  LogOut,
  Layers,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user, isRecruiter, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const candidateLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/resumes/analyze', label: 'Resume Analyzer', icon: FileText },
    { to: '/jobs', label: 'Job Explorer', icon: Briefcase },
    { to: '/matching', label: 'Job Match Details', icon: GitCompare },
    { to: '/skill-gap', label: 'Skill Gap Analysis', icon: TrendingUp },
    { to: '/analytics', label: 'Model Analytics', icon: BarChart2 },
  ];

  const recruiterLinks = [
    { to: '/recruiter/dashboard', label: 'Recruiter Overview', icon: LayoutDashboard },
    { to: '/recruiter/candidates', label: 'Candidate Management', icon: Users },
    { to: '/recruiter/jobs', label: 'Job Management', icon: Briefcase },
    { to: '/resumes/analyze', label: 'Resume Parser', icon: FileText },
    { to: '/jobs', label: 'Job Directory', icon: Layers },
    { to: '/matching', label: 'Match Calculator', icon: GitCompare },
    { to: '/skill-gap', label: 'Skill Gap Analysis', icon: TrendingUp },
    { to: '/analytics', label: 'Model Analytics', icon: BarChart2 },
  ];

  const navLinks = isRecruiter ? recruiterLinks : candidateLinks;

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-slate-100 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:z-auto ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
          <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-sm">
            SH
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-sm tracking-wide text-white">SmartHire 2.0</span>
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
              Classical ML Portal
            </span>
          </div>
        </div>

        {/* User Role Badge */}
        {user && (
          <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-950/40">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium truncate max-w-[120px]">
                {user.full_name}
              </span>
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                  isRecruiter
                    ? 'bg-purple-950 text-purple-300 border border-purple-800'
                    : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                }`}
              >
                {user.role}
              </span>
            </div>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navLinks.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => onClose()}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600 text-white font-semibold'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom Section */}
        <div className="p-3 border-t border-slate-800 space-y-1">
          <NavLink
            to="/settings"
            onClick={() => onClose()}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`
            }
          >
            <Settings className="h-4 w-4" />
            <span>Settings & Profile</span>
          </NavLink>

          <button
            onClick={handleLogout}
            type="button"
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:bg-rose-950/40 hover:text-rose-300 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
};
