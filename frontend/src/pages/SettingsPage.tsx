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
  const { user, logout, updateProfile } = useAuth();
  const navigate = useNavigate();
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [checkingHealth, setCheckingHealth] = useState<boolean>(false);
  const [healthMsg, setHealthMsg] = useState<string | null>(null);

  // Profile Edit State
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editFullName, setEditFullName] = useState<string>(user?.full_name || '');
  const [savingProfile, setSavingProfile] = useState<boolean>(false);
  const [profileFeedback, setProfileFeedback] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileFeedback(null);
    setProfileError(null);

    const clean = editFullName.trim();
    if (clean.length < 2) {
      setProfileError('Full name must be at least 2 characters.');
      return;
    }

    setSavingProfile(true);
    try {
      await updateProfile({ full_name: clean });
      setProfileFeedback('Profile name updated successfully.');
      setIsEditing(false);
      setTimeout(() => setProfileFeedback(null), 4000);
    } catch (err: any) {
      setProfileError(err.detail || 'Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

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

      {profileFeedback && (
        <Alert type="success" onClose={() => setProfileFeedback(null)}>
          {profileFeedback}
        </Alert>
      )}

      {profileError && (
        <Alert type="error" onClose={() => setProfileError(null)}>
          {profileError}
        </Alert>
      )}

      {/* Profile Details Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
            <UserIcon className="h-5 w-5 text-indigo-600" />
            <span>User Profile Information</span>
          </h3>
          {user && !isEditing && (
            <button
              type="button"
              onClick={() => {
                setEditFullName(user.full_name);
                setIsEditing(true);
              }}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition-colors"
            >
              Edit Profile
            </button>
          )}
        </div>

        {user ? (
          <div>
            {isEditing ? (
              <form onSubmit={handleSaveProfile} className="space-y-4 p-4 rounded-lg bg-slate-50 border border-slate-200 mb-4">
                <div>
                  <label htmlFor="edit-fullname" className="block text-xs font-semibold text-slate-700 mb-1">
                    Full Name
                  </label>
                  <input
                    id="edit-fullname"
                    type="text"
                    value={editFullName}
                    onChange={(e) => setEditFullName(e.target.value)}
                    required
                    minLength={2}
                    maxLength={100}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
                  />
                </div>
                <p className="text-xs text-slate-400">
                  Note: Email address and account role are locked to maintain authentication security and audit compliance.
                </p>
                <div className="flex items-center gap-2 pt-2">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50"
                  >
                    {savingProfile ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 rounded-lg bg-white border border-slate-300 text-slate-600 text-xs font-medium hover:bg-slate-50 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}

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
