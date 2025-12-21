import Cookies from 'js-cookie'

export interface SessionData {
  user: {
    id: number
    username: string
    email: string
    role: string
    full_name?: string
  } | null
  token: string | null
  expiresAt: number | null
  // SECURITY: Credentials removed - passwords should never be stored in localStorage
  // Even with encoding, localStorage is accessible to XSS attacks
}

const SESSION_KEY = 'session_data'
const TOKEN_KEY = 'access_token'

export const SessionManager = {
  // Save session data
  // SECURITY: Credentials parameter removed - passwords should never be stored
  saveSession: (user: SessionData['user'], token: string, expiresInMinutes: number = 30) => {
    const expiresAt = Date.now() + (expiresInMinutes * 60 * 1000)
    const sessionData: SessionData = {
      user,
      token,
      expiresAt,
    }
    
    // Store in localStorage for persistence
    if (typeof window !== 'undefined') {
      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData))
    }
    
    // Also store token in cookie (for API requests)
    Cookies.set(TOKEN_KEY, token, {
      expires: expiresInMinutes / (24 * 60), // Convert minutes to days
      secure: false,
      sameSite: 'lax',
      path: '/',
    })
  },
  
  // Get Basic Auth credentials
  // SECURITY NOTE: This is deprecated - passwords should not be stored
  // Basic Auth fallback should use token refresh instead
  getBasicAuthCredentials: () => {
    // Return null - passwords are no longer stored for security reasons
    // If Bearer token fails, use token refresh mechanism instead
    return null
  },

  // Get current session
  getSession: (): SessionData | null => {
    if (typeof window === 'undefined') return null
    
    try {
      const sessionStr = localStorage.getItem(SESSION_KEY)
      if (!sessionStr) return null
      
      const session: SessionData = JSON.parse(sessionStr)
      
      // Check if session is expired
      if (session.expiresAt && Date.now() > session.expiresAt) {
        SessionManager.clearSession()
        return null
      }
      
      return session
    } catch (error) {
      console.error('Error reading session:', error)
      return null
    }
  },

  // Get user from session
  getUser: () => {
    const session = SessionManager.getSession()
    return session?.user || null
  },

  // Check if session is valid
  isSessionValid: (): boolean => {
    const session = SessionManager.getSession()
    const token = Cookies.get(TOKEN_KEY)
    
    // Both session and token must exist
    return !!(session && token && session.token === token)
  },

  // Update user data in session
  updateUser: (user: SessionData['user']) => {
    const session = SessionManager.getSession()
    if (session) {
      session.user = user
      if (typeof window !== 'undefined') {
        localStorage.setItem(SESSION_KEY, JSON.stringify(session))
      }
    }
  },

  // Clear session
  clearSession: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(SESSION_KEY)
    }
    // Only remove cookies if they exist (don't throw errors)
    try {
      Cookies.remove(TOKEN_KEY, { path: '/' })
      Cookies.remove('refresh_token', { path: '/' })
    } catch (e) {
      // Ignore cookie removal errors
    }
  },

  // Refresh session expiry
  refreshExpiry: (expiresInMinutes: number = 30) => {
    const session = SessionManager.getSession()
    if (session) {
      session.expiresAt = Date.now() + (expiresInMinutes * 60 * 1000)
      if (typeof window !== 'undefined') {
        localStorage.setItem(SESSION_KEY, JSON.stringify(session))
      }
    }
  },
}

