import React from 'react';
import { useLocation } from 'react-router-dom';

const titles = {
  '/dashboard': 'Dashboard',
  '/predict': 'Predict Customer Churn',
  '/customers': 'Customer Directory',
  '/history': 'Prediction History',
  '/analytics': 'Customer Retention Analytics',
};

export const Navbar = () => {
  const location = useLocation();
  const title = titles[location.pathname] || 'Customer Churn Prediction';

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-bold text-slate-800 tracking-tight">{title}</h1>
        <p className="text-xs text-slate-500">Telecom Customer Retention Intelligence</p>
      </div>
    </header>
  );
};

export default Navbar;
