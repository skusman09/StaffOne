'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { authAPI, Cookies } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { isAuthenticated, getUser } from '@/lib/auth'
import { SessionManager } from '@/lib/session'
import { ThemeToggle } from './ThemeToggle'

export default function Navbar() {
  const router = useRouter()
  const [sessionUser, setSessionUser] = useState(getUser())

  // Load user from session immediately
  useEffect(() => {
    const session = SessionManager.getSession()
    const token = Cookies.get('access_token')
    // Verify token matches to prevent showing wrong user
    if (session?.user && session?.token === token) {
      setSessionUser(session.user)
    } else if (session && session.token !== token) {
      // Token mismatch - clear old session
      SessionManager.clearSession()
      setSessionUser(null)
    }
  }, [])

  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: authAPI.me,
    enabled: isAuthenticated(),
    retry: false,
    initialData: sessionUser || undefined,
  })
  
  // Update session user when query data loads
  useEffect(() => {
    if (user) {
      setSessionUser(user)
    }
  }, [user])
  
  // Use query user or fallback to session user
  const displayUser = user || sessionUser

  const handleLogout = () => {
    authAPI.logout()
    router.push('/login')
  }

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/dashboard" className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                Check-In/Out
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                href="/dashboard"
                className="border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                Dashboard
              </Link>
              {displayUser?.role === 'admin' && (
                <Link
                  href="/admin"
                  className="border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Admin
                </Link>
              )}
              <Link
                href="/profile"
                className="border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
              >
                Profile
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <span className="text-gray-700 dark:text-gray-300 mr-2">{displayUser?.username || 'User'}</span>
            <button
              onClick={handleLogout}
              className="bg-indigo-600 dark:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

