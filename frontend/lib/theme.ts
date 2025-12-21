'use client'

const THEME_KEY = 'theme'
const DARK_CLASS = 'dark'

export type Theme = 'light' | 'dark' | 'system'

export const ThemeManager = {
  getTheme(): Theme {
    if (typeof window === 'undefined') return 'system'
    const stored = localStorage.getItem(THEME_KEY) as Theme
    return stored || 'system'
  },

  setTheme(theme: Theme) {
    if (typeof window === 'undefined') return
    localStorage.setItem(THEME_KEY, theme)
    this.applyTheme(theme)
  },

  applyTheme(theme: Theme) {
    if (typeof window === 'undefined') return
    
    const root = window.document.documentElement
    root.classList.remove(DARK_CLASS)

    if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add(DARK_CLASS)
    }
  },

  init() {
    if (typeof window === 'undefined') return
    this.applyTheme(this.getTheme())
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (this.getTheme() === 'system') {
        this.applyTheme('system')
      }
    })
  },
}

