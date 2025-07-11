import axios from 'axios'

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add a request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add a response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If the error is 401 and we haven't retried yet
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Try to refresh the token
        const response = await api.post('/api/v1/auth/refresh')
        const { access_token } = response.data

        localStorage.setItem('token', access_token)
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        return api(originalRequest)
      } catch (error) {
        // If refresh fails, redirect to login
        localStorage.removeItem('token')
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default api

// Auth API
export const auth = {
  login: (email: string, password: string) =>
    api.post('/api/v1/auth/token', { username: email, password }),
  register: (email: string, password: string) =>
    api.post('/api/v1/auth/register', { email, password }),
  me: () => api.get('/api/v1/auth/me'),
}

// Stocks API
export const stocks = {
  getLive: (symbols: string[]) =>
    api.get(`/api/v1/stocks/live?symbols=${symbols.join(',')}`),
  getHistory: (symbol: string) =>
    api.get(`/api/v1/stocks/history/${symbol}`),
  getWatchlist: () =>
    api.get('/api/v1/stocks/watchlist'),
  addToWatchlist: (symbol: string, notes?: string) =>
    api.post(`/api/v1/stocks/watchlist/${symbol}`, { notes }),
  removeFromWatchlist: (symbol: string) =>
    api.delete(`/api/v1/stocks/watchlist/${symbol}`),
}

// News API
export const news = {
  getTrending: () =>
    api.get('/api/v1/news/trending'),
  getStockNews: (symbol: string) =>
    api.get(`/api/v1/news/stock/${symbol}`),
  search: (query: string) =>
    api.get(`/api/v1/news/search?query=${encodeURIComponent(query)}`),
}

// Chat API
export const chat = {
  ask: (query: string) =>
    api.post('/api/v1/chat/ask', { query }),
  getHistory: () =>
    api.get('/api/v1/chat/history'),
} 