import React from 'react';

export const ProbabilityMeter = ({ probability, threshold = 0.48 }) => {
  const pct = Math.min(100, Math.max(0, probability * 100));

  let colorClass = 'from-emerald-500 to-teal-500';
  let badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let statusText = 'Low Churn Risk';

  if (probability >= 0.70) {
    colorClass = 'from-rose-500 to-red-600';
    badgeColor = 'bg-rose-50 text-rose-700 border-rose-200';
    statusText = 'High Churn Risk';
  } else if (probability >= 0.40) {
    colorClass = 'from-amber-500 to-orange-500';
    badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
    statusText = 'Medium Churn Risk';
  }

  const thresholdPct = threshold * 100;

  return (
    <div className="w-full bg-slate-50 rounded-2xl p-6 border border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Estimated Churn Probability</span>
          <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{pct.toFixed(1)}%</span>
        </div>
        <span className={`px-3 py-1.5 rounded-xl text-xs font-bold border ${badgeColor}`}>
          {statusText}
        </span>
      </div>

      {/* Progress Bar Container */}
      <div className="relative w-full h-4 bg-slate-200 rounded-full overflow-hidden shadow-inner my-3">
        <div
          className={`h-full bg-gradient-to-r ${colorClass} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
        {/* Decision Threshold Marker Line */}
        <div
          className="absolute top-0 bottom-0 w-1 bg-slate-900 z-10 shadow-sm"
          style={{ left: `${thresholdPct}%` }}
          title={`Classification Decision Threshold: ${thresholdPct}%`}
        />
      </div>

      {/* Labels below meter */}
      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 mt-2">
        <span className="text-emerald-600">0% (Safe)</span>
        <span className="text-slate-600 font-bold bg-white px-2 py-0.5 rounded border border-slate-300">
          Threshold ({thresholdPct}%)
        </span>
        <span className="text-rose-600">100% (Critical)</span>
      </div>
    </div>
  );
};
