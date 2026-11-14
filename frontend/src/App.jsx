import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';

import Dashboard from './pages/Dashboard';
import PredictChurn from './pages/PredictChurn';
import Customers from './pages/Customers';
import PredictionHistory from './pages/PredictionHistory';
import Analytics from './pages/Analytics';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Main Application under DashboardLayout (No Login Required) */}
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="predict" element={<PredictChurn />} />
          <Route path="customers" element={<Customers />} />
          <Route path="history" element={<PredictionHistory />} />
          <Route path="analytics" element={<Analytics />} />
          
          {/* Legacy / Direct Route Redirects */}
          <Route path="login" element={<Navigate to="/dashboard" replace />} />
          <Route path="model-info" element={<Navigate to="/dashboard" replace />} />
          <Route path="settings" element={<Navigate to="/dashboard" replace />} />
        </Route>

        {/* Global Catch-all redirect */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
