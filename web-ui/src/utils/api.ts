import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const auth = localStorage.getItem('viswall-auth')
  if (auth) {
    const { state } = JSON.parse(auth)
    if (state.token) {
      config.headers.Authorization = `Bearer ${state.token}`
    }
  }
  return config
})

// Handle 401 responses — except on /auth/ requests, where the caller
// owns the error (redirecting on a failed login would reload the page
// before its error banner can render).
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthRequest = error.config?.url?.startsWith('/auth/')
    if (error.response?.status === 401 && !isAuthRequest) {
      localStorage.removeItem('viswall-auth')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
