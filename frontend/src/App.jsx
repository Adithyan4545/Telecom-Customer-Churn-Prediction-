import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PredictChurn from './pages/PredictChurn';
import Customers from './pages/Customers';
import PredictionHistory from './pages/PredictionHistory';
import Analytics from './pages/Analytics';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Application Routes under DashboardLayout */}
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="predict" element={<PredictChurn />} />
            <Route path="customers" element={<Customers />} />
            <Route path="history" element={<PredictionHistory />} />
            <Route path="analytics" element={<Analytics />} />

            {/* Legacy route redirects */}
            <Route path="model-info" element={<Navigate to="/dashboard" replace />} />
            <Route path="settings" element={<Navigate to="/dashboard" replace />} />
          </Route>

          {/* Global Catch-all redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
