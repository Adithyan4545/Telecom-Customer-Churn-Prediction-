import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to every request if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Simple error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
};

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getChurnDistribution: () => api.get('/dashboard/churn-distribution'),
  getMonthlyChargesDist: () => api.get('/dashboard/monthly-charges-distribution'),
  getRecentPredictions: (limit = 5) => api.get(`/dashboard/recent-predictions?limit=${limit}`),
};

export const customersApi = {
  list: (params) => api.get('/customers', { params }),
  getById: (id) => api.get(`/customers/${id}`),
};

export const predictionApi = {
  predict: (data) => api.post('/predict', data),
  save: (data) => api.post('/predictions', data),
  listHistory: (params) => api.get('/predictions', { params }),
  getById: (id) => api.get(`/predictions/${id}`),
  delete: (id) => api.delete(`/predictions/${id}`),
  exportCSV: () => api.get('/predictions/export/csv', { responseType: 'blob' }),
};

export const analyticsApi = {
  getChurnByContract: () => api.get('/analytics/churn-by-contract'),
  getChurnByTenure: () => api.get('/analytics/churn-by-tenure'),
  getChurnByPayment: () => api.get('/analytics/churn-by-payment'),
  getChurnByInternet: () => api.get('/analytics/churn-by-internet'),
  getModelMetrics: () => api.get('/analytics/model-metrics'),
};

export const modelApi = {
  getInfo: () => api.get('/model/info'),
  getMetrics: () => api.get('/model/metrics'),
  getFeatureImportance: () => api.get('/model/feature-importance'),
};

export default api;
