'use client'

import { useState, useEffect } from 'react'
import { ToastComponent, Toast } from './Toast'
import { toast } from '@/lib/toast'

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([])

  useEffect(() => {
    const unsubscribe = toast.subscribe((newToast) => {
      setToasts(toast.getToasts())
    })

    // Initial load
    setToasts(toast.getToasts())

    return unsubscribe
  }, [])

  const handleRemove = (id: string) => {
    toast.remove(id)
    setToasts(toast.getToasts())
  }

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 w-full max-w-sm space-y-2">
      {toasts.map((toastItem) => (
        <ToastComponent key={toastItem.id} toast={toastItem} onRemove={handleRemove} />
      ))}
    </div>
  )
}

