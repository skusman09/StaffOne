'use client'

import { useEffect } from 'react'
import { ThemeManager } from '@/lib/theme'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    ThemeManager.init()
  }, [])

  return <>{children}</>
}

