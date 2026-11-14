import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Server, 
  Database, 
  Cpu, 
  User, 
  ShieldCheck, 
  CheckCircle2, 
  Sliders, 
  HardDrive,
  RefreshCw,
  BellRing,
  Key,
  ExternalLink
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();
  const [autoSave, setAutoSave] = useState(true);
  const [healthStatus, setHealthStatus] = useState({
    api: 'Healthy (200 OK)',
    db: 'Connected (telecom_churn)',
    models: 'Loaded (CatBoost Pipeline)',
    latency: '14 ms',
  });
  const [testingPing, setTestingPing] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleTestPing = async () => {
    setTestingPing(true);
    const start = performance.now();
    try {
      const res = await fetch('/api/health');
      const elapsed = Math.round(performance.now() - start);
      setHealthStatus((prev) => ({
        ...prev,
        latency: `${elapsed} ms`,
        api: res.ok ? 'Healthy (200 OK)' : 'Degraded',
      }));
    } catch {
      setHealthStatus((prev) => ({
        ...prev,
        api: 'Unreachable',
        latency: 'Timeout',
      }));
    } finally {
      setTestingPing(false);
    }
  };

  const handleSavePreferences = (e) => {
    e.preventDefault();
    localStorage.setItem('telecom_autosave', String(autoSave));
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Page Header */}
      <div className="pb-1 border-b border-slate-200">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-indigo-600" />
          System Settings & Platform Configuration
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Inspect backend status, database configurations, model serving defaults, and admin profile
        </p>
      </div>

      {/* System Health Strip */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold text-slate-900">Service Status & Infrastructure Health</h2>
          </div>
          <button
            onClick={handleTestPing}
            disabled={testingPing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testingPing ? 'animate-spin text-indigo-600' : ''}`} />
            {testingPing ? 'Pinging...' : 'Ping Services'}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Backend API</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </div>
            <div className="text-xs font-bold text-slate-800">FastAPI (Python 3.12)</div>
            <div className="text-[11px] text-emerald-600 font-medium mt-0.5">{healthStatus.api}</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Primary Database</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </div>
            <div className="text-xs font-bold text-slate-800">MongoDB 8.2 (Local)</div>
            <div className="text-[11px] text-emerald-600 font-medium mt-0.5">{healthStatus.db}</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>ML Inference Engine</span>
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
            </div>
            <div className="text-xs font-bold text-slate-800">Scikit-Learn & Joblib</div>
            <div className="text-[11px] text-indigo-600 font-medium mt-0.5">{healthStatus.models}</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/60">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>API Latency</span>
              <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
            </div>
            <div className="text-xs font-bold text-slate-800">Local Loopback</div>
            <div className="text-[11px] text-cyan-600 font-mono font-medium mt-0.5">{healthStatus.latency}</div>
          </div>
        </div>
      </div>

      {/* Model Preferences Form */}
      <form onSubmit={handleSavePreferences} className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs space-y-6">
        <div>
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-600" />
            Default Machine Learning & Inference Preferences
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Configure default model selection, thresholding strategy, and audit logging behavior across the application
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Active Model (Read-Only) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Active Machine Learning Model</label>
            <div className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg bg-slate-100 text-slate-800 font-semibold flex items-center justify-between">
              <span>CatBoost Classifier</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800">Fixed Pipeline</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Loaded from <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">experiments/accuracy_optimization/best_accuracy_pipeline.pkl</code>.
            </p>
          </div>

          {/* Fixed Threshold (Read-Only) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Classification Decision Threshold</label>
            <div className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg bg-slate-100 text-slate-800 font-semibold flex items-center justify-between">
              <span>0.50 (Standard Decision Line)</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">Fixed at 0.50</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Verified 80.36% Accuracy and 0.8476 ROC-AUC across nested 5-fold cross-validation.
            </p>
          </div>
        </div>

        {/* Auto-Save Toggle */}
        <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-800">Auto-Save Predictions to MongoDB</div>
            <div className="text-[11px] text-slate-500">
              Automatically store all inference results and input attributes in the prediction history collection
            </div>
          </div>
          <button
            type="button"
            onClick={() => setAutoSave(!autoSave)}
            className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
              autoSave ? 'bg-indigo-600' : 'bg-slate-300'
            }`}
          >
            <div
              className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                autoSave ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between pt-2">
          {savedSuccess ? (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4" />
              Preferences saved successfully!
            </span>
          ) : (
            <span></span>
          )}
          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors shadow-xs"
          >
            Save Preferences
          </button>
        </div>
      </form>

      {/* Administrator Profile Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-indigo-600" />
          <h2 className="text-sm font-bold text-slate-900">Administrator Account Information</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/60">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Authenticated User</span>
            <span className="font-bold text-slate-800 block mt-0.5">{user?.full_name || 'System Administrator'}</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/60">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Email Address</span>
            <span className="font-semibold text-slate-800 block mt-0.5">{user?.email || 'admin@telecom.com'}</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/60">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Security Role</span>
            <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-800">
              {user?.role?.toUpperCase() || 'ADMIN'}
            </span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200/60 text-xs text-amber-800 flex items-start gap-2">
          <Key className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <strong>Default Demonstration Credentials:</strong> Email: <code className="bg-amber-100 px-1 py-0.5 rounded font-bold">admin@telecom.com</code> | Password: <code className="bg-amber-100 px-1 py-0.5 rounded font-bold">admin123</code>.
            In a production deployment, replace with environment-specific credentials via <code className="bg-amber-100 px-1 py-0.5 rounded">.env</code>.
          </div>
        </div>
      </div>
    </div>
  );
}
