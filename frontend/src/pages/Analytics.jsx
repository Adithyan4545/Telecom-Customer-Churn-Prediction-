import React, { useState, useEffect } from 'react';
import { 
  BarChart2, 
  DollarSign, 
  Users, 
  AlertCircle, 
  RefreshCw,
  Award,
  CheckCircle2,
  TrendingUp,
  ShieldCheck
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  AreaChart, 
  Area 
} from 'recharts';
import { analyticsApi, dashboardApi } from '../services/api';

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [contractData, setContractData] = useState([]);
  const [tenureData, setTenureData] = useState([]);
  const [paymentData, setPaymentData] = useState([]);
  const [internetData, setInternetData] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [contractRes, tenureRes, paymentRes, internetRes] = await Promise.all([
        analyticsApi.getChurnByContract().catch(() => ({ data: [] })),
        analyticsApi.getChurnByTenure().catch(() => ({ data: [] })),
        analyticsApi.getChurnByPayment().catch(() => ({ data: [] })),
        analyticsApi.getChurnByInternet().catch(() => ({ data: [] })),
      ]);

      setContractData(contractRes.data || []);
      setTenureData(tenureRes.data || []);
      setPaymentData(paymentRes.data || []);
      setInternetData(internetRes.data || []);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BarChart2 className="w-6 h-6 text-indigo-600" />
            Customer Retention Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Visual trends across customer contracts, tenure cohorts, payment methods, and services
          </p>
        </div>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          Refresh Charts
        </button>
      </div>

      {/* Business Impact KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-xs">
          <div className="flex items-center justify-between text-indigo-100 text-sm font-semibold">
            <span>Overall Churn Rate</span>
            <Users className="w-5 h-5 opacity-80" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black">26.54%</span>
            <span className="text-xs text-indigo-200 font-bold">1,869 churners</span>
          </div>
          <p className="mt-2 text-xs text-indigo-100/90 leading-relaxed font-medium">
            Historical baseline; indicates ~1 in 4 subscribers leave without retention action.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-rose-600 to-rose-700 text-white shadow-xs">
          <div className="flex items-center justify-between text-rose-100 text-sm font-semibold">
            <span>Est. Monthly MRR At Risk</span>
            <DollarSign className="w-5 h-5 opacity-80" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black">$139,130</span>
            <span className="text-xs text-rose-200 font-bold">/ month</span>
          </div>
          <p className="mt-2 text-xs text-rose-100/90 leading-relaxed font-medium">
            Average churner spend is $74.44/mo. Early retention captures high-value revenue.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-600 text-white shadow-xs">
          <div className="flex items-center justify-between text-amber-100 text-sm font-semibold">
            <span>Month-to-Month Churn</span>
            <AlertCircle className="w-5 h-5 opacity-80" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black">42.71%</span>
            <span className="text-xs text-amber-100 font-bold">High Risk</span>
          </div>
          <p className="mt-2 text-xs text-amber-100/90 leading-relaxed font-medium">
            Subscribers without annual contracts have a 15x higher defection rate than 2-year clients.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-600 to-emerald-700 text-white shadow-xs">
          <div className="flex items-center justify-between text-emerald-100 text-sm font-semibold">
            <span>Retained Subscriber Base</span>
            <ShieldCheck className="w-5 h-5 opacity-80" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black">73.46%</span>
            <span className="text-xs text-emerald-100 font-bold">5,174 active</span>
          </div>
          <p className="mt-2 text-xs text-emerald-100/90 leading-relaxed font-medium">
            Loyal customer core with sustained subscription lifetime.
          </p>
        </div>
      </div>

      {/* Row 1: Churn by Contract & Tenure */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contract Type Bar Chart */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Churn Rate by Contract Commitment</h3>
              <p className="text-xs text-slate-400">Comparing subscriber churn percentage across contract structures</p>
            </div>
            <span className="px-2 py-0.5 text-[11px] font-semibold text-rose-700 bg-rose-50 border border-rose-200 rounded-md">
              High Impact
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={contractData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="contract" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis unit="%" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Bar dataKey="churn_rate" fill="#f43f5e" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-600 flex items-center justify-between">
            <span><strong>Takeaway:</strong> 2-year contracts drop churn rate from 42.7% to only <strong>2.8%</strong>.</span>
          </div>
        </div>

        {/* Tenure Group Area Chart */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Churn Rate Across Customer Lifecycle (Tenure)</h3>
              <p className="text-xs text-slate-400">Churn risk diminishes dramatically after the first 12 months</p>
            </div>
            <span className="px-2 py-0.5 text-[11px] font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md">
              Protective Factor
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={tenureData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="tenureGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.05}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="tenure_group" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis unit="%" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="churn_rate" stroke="#4f46e5" strokeWidth={2.5} fillOpacity={1} fill="url(#tenureGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-600 flex items-center justify-between">
            <span><strong>Takeaway:</strong> Months 0–12 present maximum risk (47.7%), dropping to <strong>9.8%</strong> for 4+ year clients.</span>
          </div>
        </div>
      </div>

      {/* Row 2: Payment Method & Internet Service Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment Method */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Churn Rate by Payment Method</h3>
              <p className="text-xs text-slate-400">Electronic check users churn at nearly 3x the rate of automated methods</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={paymentData} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" unit="%" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="payment_method" type="category" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} width={110} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Bar dataKey="churn_rate" fill="#f59e0b" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-600">
            <span>Electronic check churn is <strong>45.3%</strong>, compared to ~15.2% for automated bank transfer / credit cards.</span>
          </div>
        </div>

        {/* Internet Service Type */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Churn Rate by Internet Service Type</h3>
              <p className="text-xs text-slate-400">Fiber Optic subscribers show elevated churn despite higher spend</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={internetData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis unit="%" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Bar dataKey="churn_rate" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-600">
            <span>Fiber Optic churn is <strong>41.9%</strong> vs DSL at 19.0% and No Internet at 7.4%.</span>
          </div>
        </div>
      </div>

      {/* Strategic Retention Takeaways */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Award className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900">
            Key Subscriber Retention Insights
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              Contract Commitment Impact
            </span>
            <p className="text-slate-600 leading-relaxed">
              Month-to-month contracts account for <strong>42.7% churn</strong>, compared to just <strong>2.8% for 2-year contracts</strong>. Encouraging annual contracts provides a 15x reduction in customer defection.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              Critical First-Year Window
            </span>
            <p className="text-slate-600 leading-relaxed">
              Nearly <strong>48% of all churn</strong> takes place within the first 12 months. Proactive customer onboarding check-ins and satisfaction follow-ups during months 1–6 are crucial to establishing long-term customer relationships.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              Payment Method Friction
            </span>
            <p className="text-slate-600 leading-relaxed">
              Electronic check users churn at <strong>45.3%</strong>, nearly 3x higher than automated credit card or bank debit (~15%). Incentivizing auto-pay with a one-time statement credit eliminates recurring payment friction.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 space-y-1.5">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Fiber Optic Tech Support Bundles
            </span>
            <p className="text-slate-600 leading-relaxed">
              Fiber customers have elevated churn rates (41.9%) when they lack technical assistance. Bundling complimentary technical support and cybersecurity protection directly protects high-revenue subscriber accounts.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
