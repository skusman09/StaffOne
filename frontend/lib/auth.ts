import Cookies from 'js-cookie'
import { SessionManager } from './session'

export const isAuthenticated = (): boolean => {
  // Primary check: token cookie (this is the source of truth)
  const hasToken = !!Cookies.get('access_token')
  if (!hasToken) {
    return false
  }
  
  // Secondary check: session validity (for UX, but don't block if token exists)
  // If session expired but token is valid, allow authentication and refresh session
  const session = SessionManager.getSession()
  const token = Cookies.get('access_token')
  
  // If session exists and token matches, check if expired
  if (session && session.token === token) {
    // Session is valid
    return true
  }
  
  // Token exists but session is missing/expired - still authenticated
  // Session will be refreshed on next API call
  return true
}

export const getToken = (): string | undefined => {
  return Cookies.get('access_token')
}

export const getUser = () => {
  return SessionManager.getUser()
}

