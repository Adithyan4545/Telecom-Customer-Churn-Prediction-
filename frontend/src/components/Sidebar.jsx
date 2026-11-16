import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Zap,
  Users,
  History,
  BarChart3,
  Radio,
  LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Predict Churn', path: '/predict', icon: Zap },
  { name: 'Customers', path: '/customers', icon: Users },
  { name: 'Prediction History', path: '/history', icon: History },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
];

export const Sidebar = () => {
  const { user, logout } = useAuth();

  return (
    <aside className="w-68 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-screen border-r border-slate-800">
      {/* Brand Header */}
      <div className="h-18 flex items-center px-6 gap-3.5 border-b border-slate-800/80 bg-slate-950/50">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
          <Radio className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <span className="font-extrabold text-white text-lg tracking-tight block">TelcoPredict</span>
          <span className="text-xs text-blue-400 font-bold tracking-wide uppercase">Churn Intelligence</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        <div className="px-3 pb-2 text-xs font-bold tracking-wider text-slate-400 uppercase">
          Menu
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 font-bold border border-blue-500/30 shadow-xs'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User Info & Logout Button */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between gap-3">
        <div className="min-w-0 flex-1 pl-1">
          <p className="text-sm font-bold text-slate-100 truncate">
            {user?.name || 'Administrator'}
          </p>
          <p className="text-xs text-slate-400 truncate mt-0.5">
            {user?.email || 'admin@telecom.com'}
          </p>
        </div>
        <button
          onClick={logout}
          title="Sign Out"
          className="p-2.5 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer shrink-0"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
