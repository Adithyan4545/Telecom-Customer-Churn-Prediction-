import React from 'react';

export const KpiCard = ({ title, value, subtitle, icon: Icon, color = 'blue', trend }) => {
  const colorStyles = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
  };

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-xs hover:shadow-md transition-all">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold uppercase tracking-wider text-slate-500">{title}</span>
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center border shadow-xs ${colorStyles[color] || colorStyles.blue}`}>
          {Icon && <Icon className="w-5 h-5" />}
        </div>
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">{value}</span>
        {trend && (
          <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${trend.type === 'positive' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
            {trend.text}
          </span>
        )}
      </div>
      {subtitle && <p className="text-sm text-slate-500 mt-1.5 font-medium">{subtitle}</p>}
    </div>
  );
};
