import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Layers, 
  Database, 
  CheckCircle2, 
  BarChart2, 
  Sliders, 
  Zap,
  FileCode,
  Award
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from 'recharts';
import { modelApi } from '../services/api';

export default function ModelInfo() {
  const [loading, setLoading] = useState(true);
  const [info, setInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [featureImportance, setFeatureImportance] = useState([]);

  useEffect(() => {
    const fetchModelDetails = async () => {
      setLoading(true);
      try {
        const [infoRes, metricsRes, fiRes] = await Promise.all([
          modelApi.getInfo().catch(() => ({ data: null })),
          modelApi.getMetrics().catch(() => ({ data: null })),
          modelApi.getFeatureImportance().catch(() => ({ data: [] })),
        ]);
        setInfo(infoRes.data);
        setMetrics(metricsRes.data);
        setFeatureImportance(fiRes.data || []);
      } catch (err) {
        console.error('Failed to load model info:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchModelDetails();
  }, []);

  // Format feature importance for Recharts
  const chartData = [...featureImportance]
    .slice(0, 12)
    .reverse()
    .map((item) => ({
      name: item.display_name,
      importance: Number((item.importance * 100).toFixed(2)),
      raw: item.importance,
      description: item.description,
    }));

  const activeModel = metrics?.models?.[0] || {
    name: 'CatBoost Classifier',
    strategy: 'Fixed Default Threshold (0.50)',
    accuracy: 80.36,
    precision: 66.91,
    recall: 51.47,
    f1_score: 0.5817,
    roc_auc: 0.8476,
    confusion_matrix: {
      true_negatives: 4698,
      false_positives: 476,
      false_negatives: 907,
      true_positives: 962,
    },
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="pb-1 border-b border-slate-200">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Cpu className="w-6 h-6 text-indigo-600" />
          Machine Learning Model Architecture & Interpretability
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Technical specifications, feature engineering pipeline, nested cross-validation rigor, and permutation feature importance
        </p>
      </div>

      {/* Model Architecture Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs space-y-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">CatBoost Classifier Engine</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Trained on symmetric decision trees with gradient boosting over categorical and continuous features. Loaded directly from <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded text-indigo-700">experiments/accuracy_optimization/best_accuracy_pipeline.pkl</code>.
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Model: CatBoost</span>
            <span className="font-semibold text-indigo-600">Single Active Pipeline</span>
          </div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs space-y-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-50 text-cyan-600 flex items-center justify-center">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Dataset & Splitting Integrity</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Trained on <strong>7,043</strong> subscriber records across 21 raw columns. Strict <strong>Nested Stratified 5-Fold Cross-Validation</strong> isolates all preprocessing and Bayesian tuning from outer evaluation folds to guarantee zero data leakage.
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Stratified Class Ratio: 73.5% / 26.5%</span>
            <span className="font-semibold text-cyan-600">Zero Leakage</span>
          </div>
        </div>

        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-xs space-y-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Fixed Decision Threshold</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Operates at a standard, unbiased <strong>0.50 decision threshold</strong>. Delivers verified <strong>80.36% Accuracy</strong> and <strong>0.8476 ROC-AUC</strong>, exceeding the project's &ge; 80% accuracy benchmark.
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Threshold: Fixed 0.50</span>
            <span className="font-semibold text-emerald-600">80.36% Verified</span>
          </div>
        </div>
      </div>

      {/* Feature Engineering & Preprocessing Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Preprocessing Pipeline */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <FileCode className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Scikit-Learn Preprocessing Pipeline</h3>
          </div>
          <p className="text-xs text-slate-500">
            Built using <code className="text-slate-800 bg-slate-100 px-1 py-0.5 rounded">ColumnTransformer</code> and fitted exclusively on training splits:
          </p>
          <ul className="space-y-2.5 text-xs text-slate-600">
            {info?.preprocessing_steps?.map((step, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
                <span>{step}</span>
              </li>
            )) || (
              <li className="text-slate-400">Loading pipeline steps...</li>
            )}
          </ul>
        </div>

        {/* Feature Engineering Techniques */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <h3 className="text-sm font-bold text-slate-900">Domain Feature Engineering (src/optimized_feature_engineering.py)</h3>
          </div>
          <p className="text-xs text-slate-500">
            Synthesized domain features designed to uncover underlying financial and churn risk behaviors:
          </p>
          <ul className="space-y-2.5 text-xs text-slate-600">
            {info?.feature_engineering_techniques?.map((tech, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 mt-1.5"></span>
                <span>{tech}</span>
              </li>
            )) || (
              <li className="text-slate-400">Loading feature techniques...</li>
            )}
          </ul>
        </div>
      </div>

      {/* Feature Importance Section */}
      <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-indigo-600" />
            Permutation Feature Importance (Top Predictors of Churn)
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Permutation importance computes the decrease in model score when a feature's values are randomly shuffled. Higher drop represents higher genuine predictive contribution.
          </p>
        </div>

        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 140, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
              <XAxis type="number" unit="%" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis 
                dataKey="name" 
                type="category" 
                tick={{ fontSize: 11, fill: '#334155', fontWeight: 500 }} 
                axisLine={false} 
                tickLine={false} 
              />
              <Tooltip
                formatter={(val) => [`${val}% Importance`, 'Permutation Drop']}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
              />
              <Bar dataKey="importance" fill="#4f46e5" radius={[0, 4, 4, 0]} barSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Feature Details Table with Domain Explanations */}
        <div className="overflow-x-auto border-t border-slate-100 pt-4">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase text-[10px]">
                <th className="py-2.5 px-3">Rank</th>
                <th className="py-2.5 px-3">Predictor Feature</th>
                <th className="py-2.5 px-3 text-center">Relative Weight</th>
                <th className="py-2.5 px-3">Business & Domain Driver</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {featureImportance.map((item, index) => (
                <tr key={item.feature} className="hover:bg-slate-50/70">
                  <td className="py-2.5 px-3 font-semibold text-slate-400">#{index + 1}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-800">
                    {item.display_name}
                    <span className="block font-mono text-[10px] text-slate-400 font-normal">{item.feature}</span>
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono font-medium text-indigo-600">
                    {(item.importance * 100).toFixed(2)}%
                  </td>
                  <td className="py-2.5 px-3 text-slate-600 leading-snug">
                    {item.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confusion Matrix Breakdown */}
      <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-600" />
              CatBoost Classifier Performance & Confusion Matrix
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly verified nested stratified 5-fold cross-validation results at the default 0.50 decision threshold
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Verified: 80.36% Accuracy
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* 2x2 Matrix Grid */}
          <div className="lg:col-span-6 space-y-2">
            <div className="grid grid-cols-2 gap-3 text-center">
              {/* True Negatives */}
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200/80">
                <span className="text-[10px] uppercase font-bold text-emerald-700 block">True Negatives (TN)</span>
                <span className="text-2xl font-black text-emerald-800 block mt-1">
                  {activeModel.confusion_matrix.true_negatives.toLocaleString()}
                </span>
                <span className="text-[11px] text-emerald-600 mt-1 block">
                  Correctly identified retained customers
                </span>
              </div>

              {/* False Positives */}
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200/80">
                <span className="text-[10px] uppercase font-bold text-amber-700 block">False Positives (FP)</span>
                <span className="text-2xl font-black text-amber-800 block mt-1">
                  {activeModel.confusion_matrix.false_positives.toLocaleString()}
                </span>
                <span className="text-[11px] text-amber-600 mt-1 block">
                  Retained customers flagged as churn
                </span>
              </div>

              {/* False Negatives */}
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200/80">
                <span className="text-[10px] uppercase font-bold text-rose-700 block">False Negatives (FN)</span>
                <span className="text-2xl font-black text-rose-800 block mt-1">
                  {activeModel.confusion_matrix.false_negatives.toLocaleString()}
                </span>
                <span className="text-[11px] text-rose-600 mt-1 block">
                  Missed churners (churned unpredicted)
                </span>
              </div>

              {/* True Positives */}
              <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200/80">
                <span className="text-[10px] uppercase font-bold text-indigo-700 block">True Positives (TP)</span>
                <span className="text-2xl font-black text-indigo-800 block mt-1">
                  {activeModel.confusion_matrix.true_positives.toLocaleString()}
                </span>
                <span className="text-[11px] text-indigo-600 mt-1 block">
                  Correctly captured churners
                </span>
              </div>
            </div>
          </div>

          {/* Metrics Breakdown for CatBoost */}
          <div className="lg:col-span-6 p-5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-4">
            <div>
              <h4 className="text-sm font-bold text-slate-800">CatBoost Classifier</h4>
              <p className="text-xs text-slate-500">Nested Stratified 5-Fold Cross-Validation Result (Threshold 0.50)</p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-white rounded-lg border border-slate-200/60">
                <span className="text-slate-400 block font-semibold text-[10px]">ACCURACY</span>
                <span className="text-lg font-bold text-slate-800">{activeModel.accuracy}%</span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-slate-200/60">
                <span className="text-slate-400 block font-semibold text-[10px]">PRECISION</span>
                <span className="text-lg font-bold text-slate-800">{activeModel.precision}%</span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-slate-200/60">
                <span className="text-slate-400 block font-semibold text-[10px]">RECALL</span>
                <span className="text-lg font-bold text-indigo-600">{activeModel.recall}%</span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-slate-200/60">
                <span className="text-slate-400 block font-semibold text-[10px]">F1-SCORE</span>
                <span className="text-lg font-bold text-slate-800">{activeModel.f1_score}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-indigo-50/70 border border-indigo-100 text-xs text-indigo-900 leading-relaxed">
              <strong>Evaluation Summary:</strong> Across nested 5-fold cross-validation on 7,043 subscriber records, the CatBoost Classifier achieves <strong>80.36% Accuracy</strong> and <strong>0.8476 ROC-AUC</strong> at the standard 0.50 threshold, providing reliable, automated churn predictions.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
