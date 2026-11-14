import React, { useState, useEffect, useCallback } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  Download, 
  Trash2, 
  Eye, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  SlidersHorizontal,
  X,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { predictionApi } from '../services/api';

export default function PredictionHistory() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [pages, setPages] = useState(1);

  // Filters
  const [searchCustomerId, setSearchCustomerId] = useState('');
  const [selectedRisk, setSelectedRisk] = useState('');
  const [selectedChurn, setSelectedChurn] = useState('');
  
  // Modals & Actions
  const [selectedItem, setSelectedItem] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      };
      if (searchCustomerId.trim()) params.customer_id = searchCustomerId.trim();
      if (selectedRisk) params.risk_level = selectedRisk;
      if (selectedChurn !== '') params.churn_prediction = selectedChurn === '1';

      const response = await predictionApi.listHistory(params);
      const list = response.data.items || response.data.predictions || [];
      setPredictions(list);
      setTotal(response.data.total || 0);
      setPages(response.data.total_pages || response.data.pages || 1);
    } catch (err) {
      console.error('Failed to fetch prediction history:', err);
      setError('Failed to load prediction history. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchCustomerId, selectedRisk, selectedChurn]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchHistory();
  };

  const handleResetFilters = () => {
    setSearchCustomerId('');
    setSelectedRisk('');
    setSelectedChurn('');
    setPage(1);
  };

  const handleDelete = async (id) => {
    setDeleting(true);
    try {
      await predictionApi.delete(id);
      setDeleteConfirmId(null);
      if (selectedItem && (selectedItem._id === id || selectedItem.id === id)) {
        setSelectedItem(null);
      }
      fetchHistory();
    } catch (err) {
      console.error('Failed to delete prediction:', err);
      alert('Failed to delete prediction record.');
    } finally {
      setDeleting(false);
    }
  };

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      const response = await predictionApi.exportCSV();
      // Create download blob
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `telecom_predictions_export_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export CSV:', err);
      alert('Failed to export predictions CSV.');
    } finally {
      setExporting(false);
    }
  };

  const getRiskBadge = (level) => {
    switch (level) {
      case 'High':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span>
            High Risk
          </span>
        );
      case 'Medium':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
            Medium Risk
          </span>
        );
      case 'Low':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Low Risk
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <History className="w-6 h-6 text-indigo-600" />
            Prediction History
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Audit log of all machine learning inference records saved in MongoDB
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchHistory}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
            title="Refresh Table"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleExportCSV}
            disabled={exporting || total === 0}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 rounded-lg transition-colors shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            {exporting ? 'Exporting...' : 'Export to CSV'}
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* Customer ID Search */}
          <div className="md:col-span-4 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Customer ID (e.g. 7590-VHVEG)..."
              value={searchCustomerId}
              onChange={(e) => setSearchCustomerId(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>

          {/* Risk Level Filter */}
          <div className="md:col-span-3">
            <select
              value={selectedRisk}
              onChange={(e) => {
                setSelectedRisk(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-slate-200 rounded-lg bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-700"
            >
              <option value="">All Risk Levels</option>
              <option value="High">High Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="Low">Low Risk</option>
            </select>
          </div>

          {/* Churn Prediction Filter */}
          <div className="md:col-span-3">
            <select
              value={selectedChurn}
              onChange={(e) => {
                setSelectedChurn(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-slate-200 rounded-lg bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-slate-700"
            >
              <option value="">All Outcomes</option>
              <option value="1">Will Churn</option>
              <option value="0">Will Retain</option>
            </select>
          </div>

          {/* Filter Reset Button */}
          <div className="md:col-span-2 flex items-center gap-2">
            <button
              type="submit"
              className="w-full py-2 px-3 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors"
            >
              Apply
            </button>
            {(searchCustomerId || selectedRisk || selectedChurn) && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="py-2 px-2.5 text-xs text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                title="Reset Filters"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
          <span>Found <strong className="text-slate-800">{total}</strong> total prediction records</span>
          <span>Page {page} of {pages}</span>
        </div>
      </div>

      {/* Prediction Records Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mx-auto" />
            <p className="text-sm text-slate-500 font-medium">Loading prediction history from database...</p>
          </div>
        ) : error ? (
          <div className="py-16 text-center space-y-2">
            <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
            <p className="text-sm font-semibold text-rose-700">{error}</p>
            <button
              onClick={fetchHistory}
              className="px-3 py-1.5 text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        ) : predictions.length === 0 ? (
          <div className="py-20 text-center space-y-2">
            <History className="w-10 h-10 text-slate-300 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-700">No predictions found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Run a churn prediction on the Predict page or adjust your search filters above.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Prediction ID</th>
                  <th className="py-3 px-4">Customer ID</th>
                  <th className="py-3 px-4">Date / Time</th>
                  <th className="py-3 px-4">Model Used</th>
                  <th className="py-3 px-4 text-center">Probability</th>
                  <th className="py-3 px-4 text-center">Threshold</th>
                  <th className="py-3 px-4 text-center">Prediction</th>
                  <th className="py-3 px-4 text-center">Risk Level</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {predictions.map((item) => {
                  const itemId = item._id || item.id;
                  const probPct = (item.churn_probability * 100).toFixed(1);
                  const isChurn = item.churn_prediction;
                  return (
                    <tr key={itemId} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                        {itemId ? itemId.slice(-6).toUpperCase() : 'N/A'}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-800">
                        {item.customer_id}
                      </td>
                      <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                        {new Date(item.created_at).toLocaleString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2 py-0.5 text-[10px] font-medium bg-slate-100 text-slate-700 rounded-md">
                          {item.model_name || 'CatBoost Classifier'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-bold">
                        <span className={item.churn_probability >= 0.7 ? 'text-rose-600' : item.churn_probability >= 0.4 ? 'text-amber-600' : 'text-emerald-600'}>
                          {probPct}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono text-slate-500 text-[11px]">
                        {item.threshold.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold ${
                          isChurn 
                            ? 'bg-rose-50 text-rose-700 border border-rose-200/60' 
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                        }`}>
                          {isChurn ? 'Churn' : 'Retained'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {getRiskBadge(item.risk_level)}
                      </td>
                      <td className="py-3 px-4 text-right space-x-1 whitespace-nowrap">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(itemId)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                          title="Delete Record"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination footer */}
        {!loading && total > 0 && (
          <div className="p-3 bg-slate-50/60 border-t border-slate-200/80 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing <span className="font-semibold text-slate-800">{(page - 1) * pageSize + 1}</span> to{' '}
              <span className="font-semibold text-slate-800">{Math.min(page * pageSize, total)}</span> of{' '}
              <span className="font-semibold text-slate-800">{total}</span> records
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white text-slate-600 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs font-semibold px-2">
                Page {page} of {pages}
              </span>
              <button
                onClick={() => setPage(Math.min(pages, page + 1))}
                disabled={page >= pages}
                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white text-slate-600 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Inspection Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-slate-200">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white/95 backdrop-blur-xs px-6 py-4 border-b border-slate-200 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-xl ${selectedItem.churn_prediction ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-600'}`}>
                  {selectedItem.churn_prediction ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    Customer {selectedItem.customer_id}
                  </h3>
                  <p className="text-xs text-slate-500 font-mono">
                    ID: {selectedItem._id || selectedItem.id} • {new Date(selectedItem.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Prediction Summary KPI Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200/80">
                <div>
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">Prediction</span>
                  <div className={`text-base font-bold ${selectedItem.churn_prediction ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {selectedItem.churn_prediction ? 'Likely to Churn' : 'Likely Retained'}
                  </div>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">Probability</span>
                  <div className="text-base font-bold text-slate-800">
                    {(selectedItem.churn_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">Risk Level</span>
                  <div className="mt-0.5">{getRiskBadge(selectedItem.risk_level)}</div>
                </div>
                <div>
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">Model</span>
                  <div className="text-xs font-semibold text-slate-700 mt-1 capitalize">
                    {selectedItem.model_name} (thr: {selectedItem.threshold})
                  </div>
                </div>
              </div>

              {/* Recommended Retention Strategy */}
              {selectedItem.recommendation && (
                <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-100">
                  <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-1">
                    Automated Retention Action Plan
                  </h4>
                  <p className="text-xs text-indigo-800 leading-relaxed">
                    {selectedItem.recommendation}
                  </p>
                </div>
              )}

              {/* Input Feature Breakdown */}
              {selectedItem.input_features && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Customer Profile Attributes
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
                    {Object.entries(selectedItem.input_features).map(([key, val]) => (
                      <div key={key} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
                        <span className="text-[10px] uppercase text-slate-400 font-semibold block truncate">
                          {key}
                        </span>
                        <span className="font-medium text-slate-800 truncate block mt-0.5">
                          {String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <button
                onClick={() => {
                  setDeleteConfirmId(selectedItem._id || selectedItem.id);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete Record
              </button>
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-6 space-y-4 border border-slate-200">
            <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
              <Trash2 className="w-6 h-6" />
            </div>
            <div className="text-center">
              <h3 className="text-base font-bold text-slate-900">Delete Prediction Record?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Are you sure you want to permanently delete this prediction record from MongoDB? This action cannot be undone.
              </p>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="flex-1 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirmId)}
                disabled={deleting}
                className="flex-1 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 disabled:bg-rose-400 rounded-lg transition-colors"
              >
                {deleting ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
