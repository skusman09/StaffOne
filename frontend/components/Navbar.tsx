'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { authAPI, Cookies } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { isAuthenticated, getUser } from '@/lib/auth'
import { SessionManager } from '@/lib/session'
import { ThemeToggle } from './ThemeToggle'

// Types for Navigation
type NavItemLink = {
  type: 'link'
  name: string
  href: string
  icon: React.ReactNode
}

type NavItemGroup = {
  type: 'group'
  name: string
  icon: React.ReactNode
  children: NavItemLink[]
}

type NavItem = NavItemLink | NavItemGroup

export default function Navbar() {
  const router = useRouter()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [sessionUser, setSessionUser] = useState<any>(null)

  // UI States
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  const [currentTheme, setCurrentTheme] = useState<'light' | 'dark' | 'system'>('system')

  // Refs for click outside
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Client-side only initialization
  useEffect(() => {
    setMounted(true)
    setSessionUser(getUser())

    // Click outside handler
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setActiveDropdown(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
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
    setActiveDropdown(null)
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

  // Navigation Data Structure
  const navItems: NavItem[] = [
    {
      type: 'link',
      name: 'Dashboard',
      href: '/dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    },
    {
      type: 'group',
      name: 'My Workspace',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
      children: [
        {
          type: 'link',
          name: 'History',
          href: '/history',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        },
        {
          type: 'link',
          name: 'Calendar',
          href: '/calendar',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          )
        },
        {
          type: 'link',
          name: 'Comp-off',
          href: '/compoff',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        },
        {
          type: 'link',
          name: 'My Report',
          href: '/my-report',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )
        },
        {
          type: 'link',
          name: 'My Salary',
          href: '/my-salary',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
      ]
    },
    ...(mounted && displayUser?.role === 'admin' ? [{
      type: 'group' as const,
      name: 'Admin',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      children: [
        {
          type: 'link' as const,
          name: 'Overview',
          href: '/admin',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          )
        },
        {
          type: 'link' as const,
          name: 'Payroll',
          href: '/admin/payroll',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        },
        {
          type: 'link' as const,
          name: 'Holidays',
          href: '/admin/holidays',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          )
        },
        {
          type: 'link' as const,
          name: 'Departments',
          href: '/admin/departments',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          )
        },
        {
          type: 'link' as const,
          name: 'Comp-off',
          href: '/admin/compoff',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        },
        {
          type: 'link' as const,
          name: 'Leaves',
          href: '/admin/leaves',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          )
        },
        {
          type: 'link' as const,
          name: 'Settings',
          href: '/admin/settings',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          )
        }
      ]
    }] : []),
  ]

  const isGroupActive = (item: NavItemGroup) => {
    return item.children.some(child => pathname === child.href)
  }

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
          <div className="hidden md:flex items-center space-x-1" ref={dropdownRef}>
            {navItems.map((item, index) => {
              if (item.type === 'link') {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200
                      ${isActive
                        ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/30'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800'
                      }
                    `}
                  >
                    <span className={isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'}>
                      {item.icon}
                    </span>
                    <span>{item.name}</span>
                  </Link>
                )
              } else {
                // Dropdown Group
                const isActive = isGroupActive(item) || activeDropdown === item.name
                const isOpen = activeDropdown === item.name

                return (
                  <div key={item.name} className="relative">
                    <button
                      onClick={() => setActiveDropdown(isOpen ? null : item.name)}
                      className={`
                                flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200
                                ${isActive
                          ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/30'
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800'
                        }
                            `}
                    >
                      <span className={isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400'}>
                        {item.icon}
                      </span>
                      <span>{item.name}</span>
                      <svg
                        className={`w-4 h-4 ml-1 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {/* Dropdown Content */}
                    {isOpen && (
                      <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 overflow-hidden animate-dropdown">
                        <div className="p-1">
                          {item.children.map((child) => {
                            const isChildActive = pathname === child.href
                            return (
                              <Link
                                key={child.href}
                                href={child.href}
                                onClick={() => setActiveDropdown(null)}
                                className={`
                                                    flex items-center space-x-2 px-3 py-2.5 rounded-lg text-sm transition-colors
                                                    ${isChildActive
                                    ? 'bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-slate-200'
                                  }
                                                `}
                              >
                                <span className={isChildActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400/70'}>
                                  {child.icon}
                                </span>
                                <span>{child.name}</span>
                              </Link>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )
              }
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
          <nav className="space-y-1 flex-1 overflow-y-auto">
            <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-4 mb-2">Menu</p>
            {navItems.map((item) => {
              if (item.type === 'link') {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
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
                      {item.icon}
                    </span>
                    <span>{item.name}</span>
                  </Link>
                )
              } else {
                // Mobile Group (Expandable)
                const isActive = isGroupActive(item)
                // Auto-expand if active or if explicitly toggled (for mobile, simpler to just always show or collapsible. Let's make it simple: Group Header + Indented Children)

                return (
                  <div key={item.name} className="py-2">
                    <div className="px-4 py-2 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider flex items-center space-x-2">
                      <span>{item.icon}</span>
                      <span>{item.name}</span>
                    </div>
                    <div className="pl-4 space-y-1 mt-1 border-l-2 border-slate-100 dark:border-slate-800 ml-4">
                      {item.children.map(child => {
                        const isChildActive = pathname === child.href
                        return (
                          <Link
                            key={child.href}
                            href={child.href}
                            onClick={() => setIsMenuOpen(false)}
                            className={`
                                            flex items-center space-x-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                                            ${isChildActive
                                ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                              }
                                        `}
                          >
                            <span className={isChildActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400/70'}>
                              {child.icon}
                            </span>
                            <span>{child.name}</span>
                          </Link>
                        )
                      })}
                    </div>
                  </div>
                )
              }
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
