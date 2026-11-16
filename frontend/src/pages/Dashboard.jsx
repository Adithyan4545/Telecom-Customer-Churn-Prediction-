import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  UserX,
  UserCheck,
  TrendingDown,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { dashboardApi, analyticsApi } from '../services/api';
import { KpiCard } from '../components/KpiCard';

const COLORS = ['#2563eb', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

export const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [churnDist, setChurnDist] = useState([]);
  const [monthlyDist, setMonthlyDist] = useState([]);
  const [contractData, setContractData] = useState([]);
  const [tenureData, setTenureData] = useState([]);
  const [paymentData, setPaymentData] = useState([]);
  const [recentPreds, setRecentPreds] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [
        statsRes,
        churnRes,
        monthlyRes,
        contractRes,
        tenureRes,
        paymentRes,
        recentRes,
      ] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getChurnDistribution(),
        dashboardApi.getMonthlyChargesDist(),
        analyticsApi.getChurnByContract(),
        analyticsApi.getChurnByTenure(),
        analyticsApi.getChurnByPayment(),
        dashboardApi.getRecentPredictions(5),
      ]);

      setStats(statsRes.data);
      setChurnDist(churnRes.data);
      setMonthlyDist(monthlyRes.data);
      setContractData(contractRes.data);
      setTenureData(tenureRes.data);
      setPaymentData(paymentRes.data);
      setRecentPreds(recentRes.data);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-500 font-medium">Aggregating live customer intelligence...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Title & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">Executive Telecommunications Overview</h2>
          <p className="text-sm text-slate-500 mt-1 font-medium">
            Real-time subscriber churn statistics and machine learning inference telemetry
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="px-4 py-2.5 rounded-xl bg-white border border-slate-300 text-sm font-semibold text-slate-700 hover:bg-slate-50 shadow-xs flex items-center gap-2 cursor-pointer transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-slate-500" />
            <span>Refresh Data</span>
          </button>
          <Link
            to="/predict"
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Predict Customer Churn</span>
          </Link>
        </div>
      </div>

      {/* 6 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard
          title="Total Customers"
          value={stats?.total_customers?.toLocaleString() || '7,043'}
          subtitle="Telco Subscriber Base"
          icon={Users}
          color="blue"
        />
        <KpiCard
          title="Churned Customers"
          value={stats?.churned_customers?.toLocaleString() || '1,869'}
          subtitle="Lost Subscriptions"
          icon={UserX}
          color="rose"
        />
        <KpiCard
          title="Active Customers"
          value={stats?.active_customers?.toLocaleString() || '5,174'}
          subtitle="Retained Base"
          icon={UserCheck}
          color="emerald"
        />
        <KpiCard
          title="Dataset Churn Rate"
          value={`${stats?.churn_rate || '26.54'}%`}
          subtitle="Historical Baseline"
          icon={TrendingDown}
          color="amber"
        />
        <KpiCard
          title="Total Predictions"
          value={stats?.total_predictions?.toLocaleString() || '0'}
          subtitle="Stored in MongoDB"
          icon={Sparkles}
          color="purple"
        />
        <KpiCard
          title="High Risk Flagged"
          value={stats?.high_risk_predictions?.toLocaleString() || '0'}
          subtitle="Probability >= 70%"
          icon={AlertTriangle}
          color="rose"
        />
      </div>

      {/* Charts Grid: Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pie Chart: Churn vs Non-Churn */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Subscriber Churn Distribution</h3>
              <p className="text-xs text-slate-400">Class balance in historical dataset</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={churnDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {churnDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name, props) => [`${value.toLocaleString()} (${props.payload.percentage}%)`, name]}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart: Monthly Charges Distribution */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs lg:col-span-2 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Churn Rate by Monthly Charges Bracket</h3>
              <p className="text-xs text-slate-400">Shows how price sensitivity impacts churn probability</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" domain={[0, 50]} />
                <Tooltip
                  formatter={(val, name) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="churn_rate" fill="#6366f1" radius={[8, 8, 0, 0]} name="Churn Rate %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Grid: Row 2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Contract Type Churn */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <h3 className="font-bold text-slate-800 text-sm mb-1">Churn by Contract Type</h3>
          <p className="text-xs text-slate-400 mb-4">Commitment length vs defection %</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={contractData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="contract" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" domain={[0, 50]} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="churn_rate" fill="#f43f5e" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tenure Group Churn */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <h3 className="font-bold text-slate-800 text-sm mb-1">Churn by Customer Tenure</h3>
          <p className="text-xs text-slate-400 mb-4">Customer lifecycle attrition hazard</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tenureData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="tenure_group" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" domain={[0, 60]} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="churn_rate" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Payment Method Churn */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
          <h3 className="font-bold text-slate-800 text-sm mb-1">Churn by Payment Channel</h3>
          <p className="text-xs text-slate-400 mb-4">Electronic check vs automated billing</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={paymentData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="payment_method" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" domain={[0, 60]} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Churn Rate']}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="churn_rate" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Predictions Table */}
      <div className="bg-white rounded-2xl p-6 md:p-7 border border-slate-200/90 shadow-xs">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="font-bold text-slate-900 text-base md:text-lg">Recent Real-Time Predictions</h3>
            <p className="text-sm text-slate-500">Live inference records stored securely in MongoDB</p>
          </div>
          <Link
            to="/history"
            className="text-sm font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5"
          >
            <span>View Full History</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {recentPreds.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-sm">
            No predictions generated yet. Navigate to "Predict Customer Churn" to evaluate customer records.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-xs border-b border-slate-200 select-none">
                <tr>
                  <th className="py-3.5 px-4">Customer ID</th>
                  <th className="py-3.5 px-4">Model Used</th>
                  <th className="py-3.5 px-4">Churn Probability</th>
                  <th className="py-3.5 px-4">Prediction</th>
                  <th className="py-3.5 px-4">Risk Category</th>
                  <th className="py-3.5 px-4">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {recentPreds.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">{item.customer_id}</td>
                    <td className="py-3.5 px-4 text-slate-600 truncate max-w-xs">{item.model_name}</td>
                    <td className="py-3.5 px-4 font-black text-slate-900 text-base">{item.churn_percentage}%</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-3 py-1 rounded-full font-bold text-xs ${
                          item.predicted_class === 1
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {item.predicted_label}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-3 py-1 rounded-full font-bold text-xs border ${
                          item.risk_level === 'High Risk'
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : item.risk_level === 'Medium Risk'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}
                      >
                        {item.risk_level}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 text-xs font-semibold">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
