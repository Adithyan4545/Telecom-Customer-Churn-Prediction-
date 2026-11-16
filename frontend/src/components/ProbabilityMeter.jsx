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
    <div className="w-full bg-slate-50/80 rounded-2xl p-6 border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-sm font-bold text-slate-500 uppercase tracking-wider block">Estimated Churn Probability</span>
          <span className="text-4xl font-black text-slate-900 tracking-tight mt-0.5 block">{pct.toFixed(1)}%</span>
        </div>
        <span className={`px-4 py-2 rounded-xl text-sm font-extrabold border shadow-xs ${badgeColor}`}>
          {statusText}
        </span>
      </div>

      {/* Progress Bar Container */}
      <div className="relative w-full h-5 bg-slate-200 rounded-full overflow-hidden shadow-inner my-4">
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
      <div className="flex items-center justify-between text-xs font-bold text-slate-500 mt-2">
        <span className="text-emerald-700 font-bold">0% (Low Risk)</span>
        <span className="text-slate-700 font-extrabold bg-white px-2.5 py-1 rounded-md border border-slate-300 shadow-2xs">
          Threshold ({thresholdPct}%)
        </span>
        <span className="text-rose-700 font-bold">100% (High Risk)</span>
      </div>
    </div>
  );
};
