import axios from 'axios'
import Cookies from 'js-cookie'
import { SessionManager } from './session'

// Import Cookies for use in dashboard
export { Cookies }

// Track login time to prevent immediate logout
let lastLoginTime: number | null = null
const LOGIN_GRACE_PERIOD = 5000 // 5 seconds grace period after login

const getBaseUrl = () => {
  let url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  // If no protocol is specified, default to https (or http for localhost)
  if (!url.startsWith('http')) {
    if (url.includes('localhost') || url.includes('127.0.0.1')) {
      url = `http://${url}`
    } else {
      url = `https://${url}`
    }
  }

  // Ensure no trailing slash
  return url.endsWith('/') ? url.slice(0, -1) : url
}

const API_URL = getBaseUrl()

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds timeout
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token')
    if (token) {
      // Clean the token (remove any whitespace)
      const cleanToken = token.trim()
      config.headers.Authorization = `Bearer ${cleanToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle network errors (backend not running, CORS, etc.)
    if (error.code === 'ECONNABORTED' || error.message === 'Network Error' || !error.response) {
      console.error('Network error:', error.message)
      return Promise.reject({
        ...error,
        response: {
          data: {
            detail: 'Unable to connect to server. Please make sure the backend is running on port 8001.'
          }
        }
      })
    }

    if (error.response?.status === 401) {
      // Check if we're in the grace period after login
      const timeSinceLogin = lastLoginTime ? Date.now() - lastLoginTime : Infinity
      const inGracePeriod = timeSinceLogin < LOGIN_GRACE_PERIOD

      if (inGracePeriod) {
        return Promise.reject(error)
      }

      // Only clear tokens and redirect if we're not on login/register pages
      if (typeof window !== 'undefined') {
        const currentPath = window.location.pathname
        if (!currentPath.includes('/login') && !currentPath.includes('/register')) {
          SessionManager.clearSession()
          Cookies.remove('access_token')
          Cookies.remove('refresh_token')
          lastLoginTime = null
          setTimeout(() => {
            window.location.href = '/login'
          }, 1000)
        }
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: async (data: { email: string; username: string; password: string; full_name?: string }) => {
    const response = await api.post('/auth/register', data)
    return response.data
  },
  login: async (data: { username: string; password: string }) => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('session_data')
    }

    const response = await api.post('/auth/login', data)
    if (response.data.access_token) {
      const token = response.data.access_token

      Cookies.set('access_token', token, {
        expires: 1,
        secure: false,
        sameSite: 'lax',
        path: '/'
      })
      Cookies.set('refresh_token', response.data.refresh_token, {
        expires: 7,
        secure: false,
        sameSite: 'lax',
        path: '/'
      })

      lastLoginTime = Date.now()

      const storedToken = Cookies.get('access_token')
      if (!storedToken) {
        throw new Error('Failed to store authentication token')
      }

      SessionManager.saveSession(null, token, 30)

      try {
        const userResponse = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        })
        SessionManager.saveSession(userResponse.data, token, 30)
      } catch {
        SessionManager.saveSession(null, token, 30)
      }
    } else {
      throw new Error('Login response missing access token')
    }
    return response.data
  },
  me: async () => {
    const response = await api.get('/auth/me')
    const token = Cookies.get('access_token')
    if (token) {
      const session = SessionManager.getSession()
      if (session && session.token === token) {
        SessionManager.updateUser(response.data)
        SessionManager.refreshExpiry(30)
      } else {
        SessionManager.saveSession(response.data, token, 30)
      }
    }
    return response.data
  },
  logout: () => {
    SessionManager.clearSession()
    Cookies.remove('access_token')
    Cookies.remove('refresh_token')
    lastLoginTime = null
  },
}

// Attendance API
export const attendanceAPI = {
  checkIn: async (data?: { latitude?: number; longitude?: number; device_info?: string; shift_type?: string }) => {
    const response = await api.post('/attendance/check-in', data || {})
    return response.data
  },
  checkOut: async (data?: { latitude?: number; longitude?: number; device_info?: string }) => {
    const response = await api.post('/attendance/check-out', data || {})
    return response.data
  },
  getTodayStatus: async () => {
    const response = await api.get('/attendance/my-today')
    return response.data
  },
  getHistory: async (skip = 0, limit = 100) => {
    const response = await api.get(`/attendance/history?skip=${skip}&limit=${limit}`)
    return response.data
  },
  getWorkingHours: async (days = 30) => {
    const response = await api.get(`/attendance/working-hours?days=${days}`)
    return response.data
  },
}

// Admin API
export const adminAPI = {
  getUsers: async (skip = 0, limit = 100) => {
    const response = await api.get(`/admin/users?skip=${skip}&limit=${limit}`)
    return response.data
  },
  getAttendance: async (skip = 0, limit = 100, userId?: number, pendingOnly = false) => {
    let url = `/admin/attendance?skip=${skip}&limit=${limit}`
    if (userId) url += `&user_id=${userId}`
    if (pendingOnly) url += `&pending_only=true`
    const response = await api.get(url)
    return response.data
  },
  manualCheckout: async (recordId: number, data: { checkout_time?: string; admin_notes?: string }) => {
    const response = await api.patch(`/admin/attendance/${recordId}/checkout`, data)
    return response.data
  },
  triggerAutoCheckout: async () => {
    const response = await api.post('/admin/attendance/auto-checkout')
    return response.data
  },
  updateNotes: async (recordId: number, notes: string) => {
    const response = await api.patch(`/admin/attendance/${recordId}/notes?admin_notes=${encodeURIComponent(notes)}`)
    return response.data
  },
}

// Location API
export const locationAPI = {
  getAll: async (activeOnly = false) => {
    const response = await api.get(`/locations?active_only=${activeOnly}`)
    return response.data
  },
  get: async (id: number) => {
    const response = await api.get(`/locations/${id}`)
    return response.data
  },
  create: async (data: { name: string; address?: string; latitude: number; longitude: number; radius_meters?: number }) => {
    const response = await api.post('/locations', data)
    return response.data
  },
  update: async (id: number, data: { name?: string; address?: string; latitude?: number; longitude?: number; radius_meters?: number; is_active?: boolean }) => {
    const response = await api.put(`/locations/${id}`, data)
    return response.data
  },
  delete: async (id: number) => {
    const response = await api.delete(`/locations/${id}`)
    return response.data
  },
  validate: async (latitude: number, longitude: number) => {
    const response = await api.post(`/locations/validate?latitude=${latitude}&longitude=${longitude}`)
    return response.data
  },
}

// Leave API
export const leaveAPI = {
  create: async (data: { leave_type: string; start_date: string; end_date: string; reason?: string }) => {
    const response = await api.post('/leaves', data)
    return response.data
  },
  getMyLeaves: async (skip = 0, limit = 100, status?: string) => {
    let url = `/leaves?skip=${skip}&limit=${limit}`
    if (status) url += `&status_filter=${status}`
    const response = await api.get(url)
    return response.data
  },
  getStats: async () => {
    const response = await api.get('/leaves/stats')
    return response.data
  },
  get: async (id: number) => {
    const response = await api.get(`/leaves/${id}`)
    return response.data
  },
  cancel: async (id: number) => {
    const response = await api.delete(`/leaves/${id}`)
    return response.data
  },
  // Admin endpoints
  getAll: async (skip = 0, limit = 100, status?: string, userId?: number) => {
    let url = `/leaves/admin/all?skip=${skip}&limit=${limit}`
    if (status) url += `&status_filter=${status}`
    if (userId) url += `&user_id=${userId}`
    const response = await api.get(url)
    return response.data
  },
  approve: async (id: number, data: { admin_remarks?: string }) => {
    const response = await api.patch(`/leaves/${id}/approve`, data)
    return response.data
  },
  reject: async (id: number, data: { admin_remarks?: string }) => {
    const response = await api.patch(`/leaves/${id}/reject`, data)
    return response.data
  },
}

// Analytics API
export const analyticsAPI = {
  getDashboard: async (days = 7) => {
    const response = await api.get(`/analytics/dashboard?days=${days}`)
    return response.data
  },
  getMyStats: async (days = 30) => {
    const response = await api.get(`/analytics/my-stats?days=${days}`)
    return response.data
  },
  getUserStats: async (userId: number, days = 30) => {
    const response = await api.get(`/analytics/user/${userId}?days=${days}`)
    return response.data
  },
  getTrends: async (days = 30) => {
    const response = await api.get(`/analytics/trends?days=${days}`)
    return response.data
  },
  getLeaderboard: async (days = 30, limit = 10) => {
    const response = await api.get(`/analytics/leaderboard?days=${days}&limit=${limit}`)
    return response.data
  },
}

// Notifications API
export const notificationsAPI = {
  getPreferences: async () => {
    const response = await api.get('/notifications/preferences')
    return response.data
  },
  updatePreferences: async (data: Record<string, any>) => {
    const response = await api.patch('/notifications/preferences', data)
    return response.data
  },
  getAll: async (skip = 0, limit = 50, unreadOnly = false) => {
    const response = await api.get(`/notifications?skip=${skip}&limit=${limit}&unread_only=${unreadOnly}`)
    return response.data
  },
  getCount: async () => {
    const response = await api.get('/notifications/count')
    return response.data
  },
  markAsRead: async (id: number) => {
    const response = await api.patch(`/notifications/${id}/read`)
    return response.data
  },
  markAllAsRead: async () => {
    const response = await api.post('/notifications/read-all')
    return response.data
  },
  delete: async (id: number) => {
    const response = await api.delete(`/notifications/${id}`)
    return response.data
  },
}

export default api

