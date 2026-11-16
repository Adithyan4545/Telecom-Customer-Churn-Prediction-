import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Save,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  User,
  CreditCard,
  Wifi,
  Shield,
  Info,
  Plus,
  ArrowRight
} from 'lucide-react';
import { predictionApi } from '../services/api';
import { ProbabilityMeter } from '../components/ProbabilityMeter';

const incrementCustomerId = (currentId) => {
  if (!currentId) return 'CUST-10493';
  const match = currentId.match(/(CUST-?)(\d+)/i);
  if (match) {
    const prefix = match[1];
    const num = parseInt(match[2], 10) + 1;
    const padLength = match[2].length;
    return `${prefix}${String(num).padStart(padLength, '0')}`;
  }
  const anyDigits = currentId.match(/(\d+)/);
  if (anyDigits) {
    const num = parseInt(anyDigits[1], 10) + 1;
    return currentId.replace(anyDigits[1], String(num).padStart(anyDigits[1].length, '0'));
  }
  return `${currentId}-1`;
};

const initialFormData = {
  gender: 'Female',
  SeniorCitizen: 0,
  Partner: 'No',
  Dependents: 'No',
  tenure: 12,
  PhoneService: 'Yes',
  MultipleLines: 'No',
  InternetService: 'Fiber optic',
  OnlineSecurity: 'No',
  OnlineBackup: 'No',
  DeviceProtection: 'No',
  TechSupport: 'No',
  StreamingTV: 'No',
  StreamingMovies: 'No',
  Contract: 'Month-to-month',
  PaperlessBilling: 'Yes',
  PaymentMethod: 'Electronic check',
  MonthlyCharges: 70.0,
  TotalCharges: 840.0,
};

export const PredictChurn = () => {
  const [formData, setFormData] = useState(initialFormData);
  const [customerId, setCustomerId] = useState(() => {
    return localStorage.getItem('telecom_current_cust_id') || 'CUST-10493';
  });
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchNextId = async () => {
      try {
        const res = await predictionApi.getNextId();
        if (res.data?.next_customer_id) {
          const next = res.data.next_customer_id;
          const currentLocal = localStorage.getItem('telecom_current_cust_id');
          // If local is not set or smaller than server next ID, use server's next ID
          if (!currentLocal || currentLocal === 'CUST-10492') {
            setCustomerId(next);
            localStorage.setItem('telecom_current_cust_id', next);
          }
        }
      } catch (e) {
        console.warn('Could not fetch next customer ID from server, using local sequence', e);
      }
    };
    fetchNextId();
  }, []);

  const handleChange = (field, value) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: value };
      // Auto-recalculate TotalCharges safely if tenure changes
      if (field === 'tenure' && Number(value) === 0) {
        updated.TotalCharges = 0.0;
      } else if (field === 'tenure' || field === 'MonthlyCharges') {
        const t = Number(field === 'tenure' ? value : prev.tenure);
        const m = Number(field === 'MonthlyCharges' ? value : prev.MonthlyCharges);
        if (t > 0 && m > 0 && (prev.TotalCharges === 0 || prev.TotalCharges === prev.tenure * prev.MonthlyCharges)) {
          updated.TotalCharges = Number((t * m).toFixed(2));
        }
      }
      return updated;
    });
  };

  const handleReset = () => {
    setFormData(initialFormData);
    const nextId = incrementCustomerId(customerId);
    setCustomerId(nextId);
    localStorage.setItem('telecom_current_cust_id', nextId);
    setPrediction(null);
    setSavedSuccess(false);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSavedSuccess(false);

    try {
      const payload = {
        customer_id: customerId.trim() || undefined,
        features: {
          ...formData,
          tenure: Number(formData.tenure),
          MonthlyCharges: Number(formData.MonthlyCharges),
          TotalCharges: Number(formData.TotalCharges),
          SeniorCitizen: Number(formData.SeniorCitizen),
        },
        save_to_db: false,
      };

      const res = await predictionApi.predict(payload);
      setPrediction(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToDb = async () => {
    if (!prediction) return;
    setSaveLoading(true);
    try {
      await predictionApi.save({
        customer_id: prediction.customer_id,
        customer_features: formData,
        predicted_class: prediction.predicted_class,
        churn_probability: prediction.churn_probability,
        risk_level: prediction.risk_level,
        model_name: prediction.model_name,
        threshold: prediction.threshold,
      });
      setSavedSuccess(true);
      // Auto-increment customerId for the next customer
      const nextId = incrementCustomerId(prediction.customer_id || customerId);
      setCustomerId(nextId);
      localStorage.setItem('telecom_current_cust_id', nextId);
    } catch (err) {
      setError('Failed to save prediction record.');
    } finally {
      setSaveLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900">
            Predict Customer Churn
          </h1>
          <p className="text-base text-slate-500 mt-1">
            Enter customer details to calculate real-time churn likelihood with machine learning
          </p>
        </div>
        <button
          type="button"
          onClick={handleReset}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RotateCcw className="w-4 h-4 text-slate-500" />
          Reset Form
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center gap-2.5">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Form (Left) & Prediction Result (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Form Column */}
        <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-6">
          {/* Section 1: Customer Profile & Demographics */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs space-y-5">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <User className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">
                1. Customer Profile & Demographics
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-sm font-semibold text-slate-700">Customer Identifier</label>
                  <button
                    type="button"
                    onClick={() => {
                      const next = incrementCustomerId(customerId);
                      setCustomerId(next);
                      localStorage.setItem('telecom_current_cust_id', next);
                    }}
                    title="Advance to next customer ID (+1)"
                    className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded-lg cursor-pointer transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Next ID</span>
                  </button>
                </div>
                <div className="relative">
                  <input
                    type="text"
                    value={customerId}
                    onChange={(e) => {
                      setCustomerId(e.target.value);
                      localStorage.setItem('telecom_current_cust_id', e.target.value);
                    }}
                    placeholder="e.g. CUST-10493"
                    className="w-full pl-3.5 pr-28 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-bold text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 font-mono transition-all"
                  />
                  <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-md border border-emerald-300 pointer-events-none">
                    Auto-Increment
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Gender</label>
                <select
                  value={formData.gender}
                  onChange={(e) => handleChange('gender', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Senior Citizen</label>
                <select
                  value={formData.SeniorCitizen}
                  onChange={(e) => handleChange('SeniorCitizen', Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value={0}>No (Age under 65)</option>
                  <option value={1}>Yes (Senior Citizen)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Has Partner</label>
                <select
                  value={formData.Partner}
                  onChange={(e) => handleChange('Partner', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Has Dependents</label>
                <select
                  value={formData.Dependents}
                  onChange={(e) => handleChange('Dependents', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: Contract & Billing */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs space-y-5">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <CreditCard className="w-5 h-5 text-emerald-600" />
              <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">
                2. Subscription Terms & Billing
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                  Customer Tenure (Months: {formData.tenure})
                </label>
                <input
                  type="number"
                  min="0"
                  max="72"
                  value={formData.tenure}
                  onChange={(e) => handleChange('tenure', Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Contract Duration</label>
                <select
                  value={formData.Contract}
                  onChange={(e) => handleChange('Contract', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="Month-to-month">Month-to-month</option>
                  <option value="One year">One year</option>
                  <option value="Two year">Two year</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Payment Method</label>
                <select
                  value={formData.PaymentMethod}
                  onChange={(e) => handleChange('PaymentMethod', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="Electronic check">Electronic check</option>
                  <option value="Mailed check">Mailed check</option>
                  <option value="Bank transfer (automatic)">Bank transfer (automatic)</option>
                  <option value="Credit card (automatic)">Credit card (automatic)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Paperless Billing</label>
                <select
                  value={formData.PaperlessBilling}
                  onChange={(e) => handleChange('PaperlessBilling', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="Yes">Yes</option>
                  <option value="No">No</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Monthly Charges ($)</label>
                <input
                  type="number"
                  step="0.05"
                  min="18"
                  max="125"
                  value={formData.MonthlyCharges}
                  onChange={(e) => handleChange('MonthlyCharges', parseFloat(e.target.value) || 0)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Total Lifetime Charges ($)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={formData.TotalCharges}
                  onChange={(e) => handleChange('TotalCharges', parseFloat(e.target.value) || 0)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Telecommunication Services */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs space-y-5">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <Wifi className="w-5 h-5 text-cyan-600" />
              <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">
                3. Internet & Phone Services
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Phone Service</label>
                <select
                  value={formData.PhoneService}
                  onChange={(e) => handleChange('PhoneService', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="Yes">Yes</option>
                  <option value="No">No</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Multiple Lines</label>
                <select
                  value={formData.MultipleLines}
                  onChange={(e) => handleChange('MultipleLines', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No phone service">No phone service</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Internet Service</label>
                <select
                  value={formData.InternetService}
                  onChange={(e) => handleChange('InternetService', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="Fiber optic">Fiber optic</option>
                  <option value="DSL">DSL</option>
                  <option value="No">No Internet</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 4: Security & Digital Add-ons */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs space-y-5">
            <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
              <Shield className="w-5 h-5 text-purple-600" />
              <h3 className="font-bold text-slate-800 text-sm uppercase tracking-wider">
                4. Digital Add-ons & Support
              </h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Online Security</label>
                <select
                  value={formData.OnlineSecurity}
                  onChange={(e) => handleChange('OnlineSecurity', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No internet service">No internet</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Online Backup</label>
                <select
                  value={formData.OnlineBackup}
                  onChange={(e) => handleChange('OnlineBackup', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No internet service">No internet</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Device Protection</label>
                <select
                  value={formData.DeviceProtection}
                  onChange={(e) => handleChange('DeviceProtection', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No internet service">No internet</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Tech Support</label>
                <select
                  value={formData.TechSupport}
                  onChange={(e) => handleChange('TechSupport', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No internet service">No internet</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Streaming TV</label>
                <select
                  value={formData.StreamingTV}
                  onChange={(e) => handleChange('StreamingTV', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No internet service">No internet</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">Streaming Movies</label>
                <select
                  value={formData.StreamingMovies}
                  onChange={(e) => handleChange('StreamingMovies', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                  <option value="No internet service">No internet</option>
                </select>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 px-6 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold text-base rounded-2xl shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2.5 cursor-pointer"
          >
            <Sparkles className="w-5 h-5" />
            <span>{loading ? 'Evaluating Churn Risk with CatBoost Pipeline...' : 'Predict Customer Churn'}</span>
          </button>
        </form>

        {/* Prediction Results Column */}
        <div className="lg:col-span-5 sticky top-20">
          {prediction ? (
            <div className="bg-white rounded-2xl p-6 md:p-7 border border-slate-200/90 shadow-sm space-y-6 animate-in fade-in duration-200">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Machine Learning Analysis</span>
                <h3 className="text-xl md:text-2xl font-black text-slate-900 mt-1">
                  {prediction.predicted_label === 'Churn' ? (
                    <span className="text-rose-600 flex items-center gap-2">
                      <AlertTriangle className="w-6 h-6 text-rose-600" />
                      Customer At Risk of Leaving
                    </span>
                  ) : (
                    <span className="text-emerald-600 flex items-center gap-2">
                      <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                      Customer Likely to Stay
                    </span>
                  )}
                </h3>
              </div>

              {/* Visual Probability Meter */}
              <ProbabilityMeter
                probability={prediction.churn_probability}
                threshold={0.50}
              />

              {/* Simple Details Breakdown */}
              <div className="grid grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200 text-sm">
                <div>
                  <span className="text-xs text-slate-500 block font-semibold uppercase tracking-wider">Customer ID</span>
                  <span className="font-mono font-bold text-slate-900 text-base mt-1 block truncate">
                    {prediction.customer_id}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 block font-semibold uppercase tracking-wider">Risk Category</span>
                  <span className={`font-bold text-base mt-1 block ${
                    prediction.risk_level === 'High Risk' ? 'text-rose-600' : prediction.risk_level === 'Medium Risk' ? 'text-amber-600' : 'text-emerald-600'
                  }`}>
                    {prediction.risk_level}
                  </span>
                </div>
              </div>

              {/* Save Prediction Button */}
              <div className="pt-2">
                {savedSuccess ? (
                  <div className="space-y-3">
                    <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold text-sm flex items-center justify-center gap-2.5">
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      <span>Successfully Saved to Prediction History</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setPrediction(null);
                        setSavedSuccess(false);
                      }}
                      className="w-full py-3.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-md flex items-center justify-center gap-2 cursor-pointer transition-colors"
                    >
                      <span>Evaluate Next Customer ({customerId})</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={handleSaveToDb}
                    disabled={saveLoading}
                    className="w-full py-3.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm shadow-md flex items-center justify-center gap-2 cursor-pointer transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    <span>{saveLoading ? 'Saving...' : 'Save Prediction to History'}</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-10 border-2 border-dashed border-slate-200 text-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 mx-auto flex items-center justify-center">
                <Sparkles className="w-7 h-7" />
              </div>
              <h3 className="font-bold text-slate-800 text-base">Awaiting Customer Profile</h3>
              <p className="text-sm text-slate-500 max-w-xs mx-auto leading-relaxed">
                Fill in the customer information on the left and click "Predict Customer Churn" to see real-time churn analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictChurn;
