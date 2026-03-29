'use client'

import { Toast, ToastType } from '@/components/Toast'

type ToastCallback = (toast: Toast) => void

class ToastManager {
  private listeners: ToastCallback[] = []
  private toasts: Toast[] = []

  subscribe(callback: ToastCallback) {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  private notify() {
    this.listeners.forEach((callback) => {
      callback(this.toasts[this.toasts.length - 1] || null)
    })
  }

  dismissAll() {
    this.toasts = []
    this.notify()
  }

  show(message: string, type: ToastType = 'info', duration?: number) {
    // Robust duplicate prevention
    if (this.toasts.some(t => t.message === message)) {
      this.toasts = this.toasts.filter(t => t.message !== message)
    }

    const toast: Toast = {
      id: Math.random().toString(36).substr(2, 9),
      message,
      type,
      duration,
    }
    
    this.toasts.push(toast)
    
    // Safety limit to prevent UX clutter
    if (this.toasts.length > 4) {
      this.toasts.shift()
    }

    this.notify()
    return toast.id
  }

  success(message: string, duration?: number) {
    // Clear all error toasts when a success occurs to signal resolution
    this.toasts = this.toasts.filter(t => t.type !== 'error')
    return this.show(message, 'success', duration)
  }

  error(message: string, duration?: number) {
    // Error duration is slightly longer for better readability
    return this.show(message, 'error', duration || 6000)
  }

  info(message: string, duration?: number) {
    return this.show(message, 'info', duration)
  }

  warning(message: string, duration?: number) {
    return this.show(message, 'warning', duration)
  }

  remove(id: string) {
    this.toasts = this.toasts.filter((toast) => toast.id !== id)
    this.notify()
  }

  getToasts(): Toast[] {
    return this.toasts
  }
}

export const toast = new ToastManager()

