import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Eye,
  RefreshCw,
  X,
  User,
  CreditCard,
  Wifi,
  FileText
} from 'lucide-react';
import { customersApi } from '../services/api';

export const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [contractFilter, setContractFilter] = useState('All');
  const [churnFilter, setChurnFilter] = useState('All');
  const [sortBy, setSortBy] = useState('tenure');
  const [sortOrder, setSortOrder] = useState('desc');
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        contract: contractFilter !== 'All' ? contractFilter : undefined,
        churn: churnFilter !== 'All' ? churnFilter : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      };
      const res = await customersApi.list(params);
      setCustomers(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      console.error('Error fetching customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [page, contractFilter, churnFilter, sortBy, sortOrder]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers();
  };

  const handleSortToggle = (col) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
  };

  const handleViewCustomer = async (cid) => {
    setModalLoading(true);
    try {
      const res = await customersApi.getById(cid);
      setSelectedCustomer(res.data);
    } catch (err) {
      console.error('Error loading customer details:', err);
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-slate-900 tracking-tight">Customer Directory</h2>
          <p className="text-sm text-slate-500 mt-1 font-medium">
            Search, filter, and inspect records from the real Telco subscriber dataset (N = 7,043)
          </p>
        </div>
        <div className="text-sm text-slate-600 font-bold bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-xs">
          Showing {customers.length} of {total.toLocaleString()} Customers
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-2xl p-4 md:p-5 border border-slate-200/90 shadow-xs flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Customer ID (e.g. 7590-VHVEG)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
          />
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {/* Contract Filter */}
          <div className="flex items-center gap-2 text-sm text-slate-700">
            <span className="font-bold text-slate-500 text-xs uppercase tracking-wider">Contract:</span>
            <select
              value={contractFilter}
              onChange={(e) => {
                setContractFilter(e.target.value);
                setPage(1);
              }}
              className="p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-bold text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="All">All Contracts</option>
              <option value="Month-to-month">Month-to-month</option>
              <option value="One year">One year</option>
              <option value="Two year">Two year</option>
            </select>
          </div>

          {/* Churn Filter */}
          <div className="flex items-center gap-2 text-sm text-slate-700">
            <span className="font-bold text-slate-500 text-xs uppercase tracking-wider">Status:</span>
            <select
              value={churnFilter}
              onChange={(e) => {
                setChurnFilter(e.target.value);
                setPage(1);
              }}
              className="p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-bold text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="All">All Status</option>
              <option value="No">Retained (No)</option>
              <option value="Yes">Churned (Yes)</option>
            </select>
          </div>

          <button
            type="button"
            onClick={fetchCustomers}
            className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 cursor-pointer transition-colors"
            title="Refresh Table"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        {loading ? (
          <div className="text-center py-16">
            <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-slate-500 font-medium">Querying subscriber records...</p>
          </div>
        ) : customers.length === 0 ? (
          <div className="text-center py-16 text-slate-400 text-sm font-medium">
            No customers found matching the search criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider text-xs border-b border-slate-200 select-none">
                <tr>
                  <th className="py-3.5 px-4">Customer ID</th>
                  <th className="py-3.5 px-4">Gender</th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-slate-900"
                    onClick={() => handleSortToggle('tenure')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Tenure</span>
                      <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                    </div>
                  </th>
                  <th className="py-3.5 px-4">Contract</th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-slate-900"
                    onClick={() => handleSortToggle('MonthlyCharges')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Monthly</span>
                      <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                    </div>
                  </th>
                  <th
                    className="py-3.5 px-4 cursor-pointer hover:text-slate-900"
                    onClick={() => handleSortToggle('TotalCharges')}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Total Charges</span>
                      <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                    </div>
                  </th>
                  <th className="py-3.5 px-4">Payment Method</th>
                  <th className="py-3.5 px-4">Actual Churn</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">{c.customer_id}</td>
                    <td className="py-3.5 px-4 text-slate-600">{c.gender}</td>
                    <td className="py-3.5 px-4 text-slate-800 font-bold">{c.tenure} mo</td>
                    <td className="py-3.5 px-4 text-slate-700">{c.Contract}</td>
                    <td className="py-3.5 px-4 text-slate-900 font-extrabold">${c.MonthlyCharges.toFixed(2)}</td>
                    <td className="py-3.5 px-4 text-slate-700 font-medium">${c.TotalCharges.toFixed(2)}</td>
                    <td className="py-3.5 px-4 text-slate-600 truncate max-w-xs">{c.PaymentMethod}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-3 py-1 rounded-full font-bold text-xs ${
                          c.actual_churn === 'Yes'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {c.actual_churn === 'Yes' ? 'Churned' : 'Retained'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleViewCustomer(c.customer_id)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 text-slate-700 text-xs font-bold inline-flex items-center gap-1.5 transition-colors cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-200 flex items-center justify-between text-sm text-slate-600 font-semibold">
          <span>
            Page <strong className="text-slate-800">{page}</strong> of <strong className="text-slate-800">{totalPages}</strong>
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-40 cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-40 cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 md:p-8 shadow-2xl border border-slate-200 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <span className="text-xs text-slate-400 font-mono block">Customer File</span>
                <h3 className="text-xl font-bold text-slate-900">{selectedCustomer.customer_id}</h3>
              </div>
              <button
                onClick={() => setSelectedCustomer(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              {Object.entries(selectedCustomer.customer_data).map(([key, val]) => (
                <div key={key} className="p-3 rounded-xl bg-slate-50 border border-slate-200/60">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
                    {key}
                  </span>
                  <span className="font-bold text-slate-800">{String(val)}</span>
                </div>
              ))}
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setSelectedCustomer(null)}
                className="px-5 py-2 rounded-xl bg-slate-900 text-white font-semibold text-xs"
              >
                Close View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;
