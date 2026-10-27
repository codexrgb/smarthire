import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User as UserIcon,
  ShieldCheck,
  Server,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getHealth } from '../api';
import type { HealthResponse } from '../api/types';
import { Alert } from '../components/common/Alert';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [checkingHealth, setCheckingHealth] = useState<boolean>(false);
  const [healthMsg, setHealthMsg] = useState<string | null>(null);

  const handleTestBackend = async () => {
    setCheckingHealth(true);
    setHealthMsg(null);
    try {
      const res = await getHealth();
      setHealthStatus(res);
      setHealthMsg('Backend connection verified successfully.');
    } catch {
      setHealthMsg('Unable to connect to SmartHire API server.');
    } finally {
      setCheckingHealth(false);
    }
  };

  const handleSignOut = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Settings & Account Profile
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Manage your session credentials, view role permissions, and test backend connectivity.
        </p>
      </div>

      {healthMsg && (
        <Alert
          type={healthStatus?.status === 'healthy' ? 'success' : 'error'}
          onClose={() => setHealthMsg(null)}
        >
          {healthMsg}
        </Alert>
      )}

      {/* Profile Details Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <h3 className="font-bold text-slate-900 text-base mb-4 flex items-center gap-2">
          <UserIcon className="h-5 w-5 text-indigo-600" />
          <span>User Profile Information</span>
        </h3>

        {user ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-400 block font-medium">Full Name</span>
              <span className="font-semibold text-slate-900 mt-0.5 block">{user.full_name}</span>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-400 block font-medium">Email Address</span>
              <span className="font-semibold text-slate-900 mt-0.5 block">{user.email}</span>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-400 block font-medium">System Role</span>
              <span className="inline-flex items-center gap-1 font-semibold text-indigo-700 capitalize mt-0.5">
                <ShieldCheck className="h-4 w-4" />
                {user.role} Account
              </span>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-400 block font-medium">Account ID</span>
              <span className="font-mono text-xs text-slate-600 mt-0.5 block select-all">
                {user.id}
              </span>
            </div>
          </div>
        ) : (
          <div className="py-6 text-center text-sm text-slate-500">
            You are browsing as an unauthenticated guest. Sign in to link resume parsing and
            recommendations to your profile.
          </div>
        )}
      </div>

      {/* Backend & Security Infrastructure */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
          <Server className="h-5 w-5 text-indigo-600" />
          <span>Backend Configuration & Connectivity</span>
        </h3>

        <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700 flex items-center justify-between flex-wrap gap-2">
          <span>Target REST Base URL:</span>
          <span className="font-bold bg-white px-2 py-1 rounded border border-slate-300">
            {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
          </span>
        </div>

        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={handleTestBackend}
            disabled={checkingHealth}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 font-semibold text-xs hover:bg-indigo-100 transition-colors"
          >
            <Server className="h-3.5 w-3.5" />
            <span>{checkingHealth ? 'Testing connection...' : 'Test Backend Connection'}</span>
          </button>

          {user && (
            <button
              type="button"
              onClick={handleSignOut}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-semibold text-xs hover:bg-rose-100 transition-colors"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
