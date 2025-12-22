'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { authAPI, Cookies } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { isAuthenticated, getUser } from '@/lib/auth'
import { SessionManager } from '@/lib/session'
import { ThemeToggle } from './ThemeToggle'

export default function Navbar() {
  const router = useRouter()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [sessionUser, setSessionUser] = useState<any>(null)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const [currentTheme, setCurrentTheme] = useState<'light' | 'dark' | 'system'>('system')

  // Client-side only initialization
  useEffect(() => {
    setMounted(true)
    setSessionUser(getUser())
  }, [])

  // Sync theme from localStorage when menu opens
  useEffect(() => {
    if (!mounted) return
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null
    if (saved) setCurrentTheme(saved)
  }, [isMenuOpen, mounted])

  useEffect(() => {
    if (!mounted) return
    const session = SessionManager.getSession()
    const token = Cookies.get('access_token')
    if (session?.user && session?.token === token) {
      setSessionUser(session.user)
    } else if (session && session.token !== token) {
      SessionManager.clearSession()
      setSessionUser(null)
    }
  }, [])

  useEffect(() => {
    setIsMenuOpen(false)
    setIsProfileOpen(false)
  }, [pathname])

  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: authAPI.me,
    enabled: isAuthenticated(),
    retry: false,
    initialData: sessionUser || undefined,
  })

  useEffect(() => {
    if (user) {
      setSessionUser(user)
    }
  }, [user])

  const displayUser = user || sessionUser

  const handleLogout = () => {
    authAPI.logout()
    router.push('/login')
  }

  // Only include admin link after client-side mount to prevent hydration mismatch
  const navLinks = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    },
    {
      name: 'History',
      href: '/history',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    ...(mounted && displayUser?.role === 'admin' ? [{
      name: 'Admin',
      href: '/admin',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    }] : []),
  ]

  return (
    <nav className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 xl:px-12 max-w-full lg:max-w-7xl xl:max-w-[90vw] 2xl:max-w-[1800px]">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/dashboard" className="group flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center transition-transform duration-200 group-hover:scale-105">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold text-slate-900 dark:text-white">
                CheckIn
              </span>
              <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 tracking-wider uppercase">
                Pro
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200
                    ${isActive
                      ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/30'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }
                  `}
                >
                  <span className={isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'}>
                    {link.icon}
                  </span>
                  <span>{link.name}</span>
                </Link>
              )
            })}
          </div>

          {/* Desktop Right Side - User Dropdown */}
          <div className="hidden md:flex items-center space-x-3">
            <ThemeToggle />

            {/* User Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-3 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer"
              >
                <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                  {(displayUser?.username || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">{displayUser?.username || 'User'}</span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">{displayUser?.role || 'Member'}</span>
                </div>
                <svg className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isProfileOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {isProfileOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setIsProfileOpen(false)} />
                  <div className="absolute right-0 mt-2 w-full min-w-[200px] bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 z-50 animate-dropdown">
                    <div className="p-2">
                      <Link
                        href="/profile"
                        onClick={() => setIsProfileOpen(false)}
                        className="flex items-center space-x-3 w-full px-3 py-2.5 rounded-lg text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                      >
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span>Profile</span>
                      </Link>
                      <div className="my-1 border-t border-slate-200 dark:border-slate-700" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center space-x-3 w-full px-3 py-2.5 rounded-lg text-sm text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <div className="w-5 flex flex-col items-center justify-center space-y-1.5">
              <span className={`block w-full h-0.5 bg-slate-600 dark:bg-slate-300 transition-all duration-300 ${isMenuOpen ? 'rotate-45 translate-y-2' : ''}`} />
              <span className={`block w-full h-0.5 bg-slate-600 dark:bg-slate-300 transition-all duration-300 ${isMenuOpen ? 'opacity-0' : ''}`} />
              <span className={`block w-full h-0.5 bg-slate-600 dark:bg-slate-300 transition-all duration-300 ${isMenuOpen ? '-rotate-45 -translate-y-2' : ''}`} />
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Side Drawer with proper open/close animations */}
      {/* Backdrop */}
      <div
        className={`md:hidden fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 ${isMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        onClick={() => setIsMenuOpen(false)}
      />

      {/* Drawer - slides from RIGHT (where hamburger is) */}
      <div
        className={`md:hidden fixed right-0 top-0 bottom-0 w-[75%] max-w-[300px] bg-white dark:bg-slate-900 z-50 shadow-2xl transition-transform duration-300 ease-out ${isMenuOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
      >
        <div className="p-5 h-full flex flex-col">
          {/* Header with close button */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-11 h-11 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                {(displayUser?.username || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{displayUser?.username || 'User'}</p>
                <p className="text-xs text-indigo-600 dark:text-indigo-400 capitalize">{displayUser?.role || 'Member'}</p>
              </div>
            </div>
            <button
              onClick={() => setIsMenuOpen(false)}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            >
              <svg className="w-5 h-5 text-slate-600 dark:text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1 flex-1">
            <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-4 mb-2">Menu</p>
            {navLinks.map((link) => {
              const isActive = pathname === link.href
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsMenuOpen(false)}
                  className={`
                    flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                    ${isActive
                      ? 'text-white bg-gradient-to-r from-indigo-600 to-violet-600 shadow-lg shadow-indigo-500/25'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                    }
                  `}
                >
                  <span className={isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400'}>
                    {link.icon}
                  </span>
                  <span>{link.name}</span>
                </Link>
              )
            })}

            {/* Profile Link */}
            <Link
              href="/profile"
              onClick={() => setIsMenuOpen(false)}
              className={`
                flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                ${pathname === '/profile'
                  ? 'text-white bg-gradient-to-r from-indigo-600 to-violet-600 shadow-lg shadow-indigo-500/25'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                }
              `}
            >
              <svg className={`w-5 h-5 ${pathname === '/profile' ? 'text-white' : 'text-slate-500 dark:text-slate-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span>Profile</span>
            </Link>
          </nav>

          {/* Bottom Actions */}
          <div className="pt-4 mt-4 border-t border-slate-200 dark:border-slate-700/50 space-y-4">
            {/* Theme Selector - Segmented Control */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-1">Theme</span>
              <div className="flex bg-slate-100 dark:bg-slate-800 rounded-xl p-1 gap-1">
                <button
                  onClick={() => {
                    setCurrentTheme('light')
                    localStorage.setItem('theme', 'light')
                    document.documentElement.classList.remove('dark')
                    document.documentElement.classList.add('light')
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${currentTheme === 'light'
                    ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  Light
                </button>
                <button
                  onClick={() => {
                    setCurrentTheme('dark')
                    localStorage.setItem('theme', 'dark')
                    document.documentElement.classList.remove('light')
                    document.documentElement.classList.add('dark')
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${currentTheme === 'dark'
                    ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  Dark
                </button>
                <button
                  onClick={() => {
                    setCurrentTheme('system')
                    localStorage.setItem('theme', 'system')
                    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
                    document.documentElement.classList.remove('light', 'dark')
                    document.documentElement.classList.add(systemTheme)
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${currentTheme === 'system'
                    ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Auto
                </button>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center justify-center space-x-2 w-full px-4 py-3 text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
