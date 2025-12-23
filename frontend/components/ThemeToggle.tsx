'use client'

import { useState, useEffect, useRef } from 'react'
import { Sun, Moon, Monitor } from 'lucide-react'

type Theme = 'light' | 'dark' | 'system'

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>('system')
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme || 'system'
    setTheme(savedTheme)
    applyTheme(savedTheme)
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const applyTheme = (newTheme: Theme) => {
    const root = window.document.documentElement

    if (newTheme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      root.classList.remove('light', 'dark')
      root.classList.add(systemTheme)
    } else {
      root.classList.remove('light', 'dark', 'system')
      root.classList.add(newTheme)
    }
  }

  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
    setIsOpen(false)
  }

  const getCurrentIcon = () => {
    if (theme === 'dark') {
      return <Moon className="w-4 h-4" />
    } else if (theme === 'light') {
      return <Sun className="w-4 h-4" />
    } else {
      return <Monitor className="w-4 h-4" />
    }
  }

  const themes = [
    {
      value: 'light' as Theme,
      label: 'Light',
      icon: <Sun className="w-5 h-5" />
    },
    {
      value: 'dark' as Theme,
      label: 'Dark',
      icon: <Moon className="w-5 h-5" />
    },
    {
      value: 'system' as Theme,
      label: 'System',
      icon: <Monitor className="w-5 h-5" />
    }
  ]

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-600 dark:text-slate-400"
        aria-label="Toggle theme"
      >
        {getCurrentIcon()}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-12 w-44 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 py-2 z-[100]">
          {themes.map((themeOption) => (
            <button
              key={themeOption.value}
              onClick={() => handleThemeChange(themeOption.value)}
              className={`
                w-full flex items-center space-x-3 px-4 py-2.5 text-sm font-medium transition-all duration-200
                ${theme === themeOption.value
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }
              `}
            >
              <span className={theme === themeOption.value ? 'text-white' : 'text-slate-400'}>
                {themeOption.icon}
              </span>
              <span>{themeOption.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
