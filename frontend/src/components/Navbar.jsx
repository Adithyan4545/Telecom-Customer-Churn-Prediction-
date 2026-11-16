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
    <header className="h-18 bg-white border-b border-slate-200/90 px-8 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      <div>
        <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight">{title}</h1>
        <p className="text-sm text-slate-500 font-medium">Telecom Customer Retention Intelligence & Prediction</p>
      </div>
    </header>
  );
};

export default Navbar;
