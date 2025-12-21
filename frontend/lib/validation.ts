export interface ValidationResult {
  isValid: boolean
  errors: string[]
}

export function validateEmail(email: string): ValidationResult {
  const errors: string[] = []
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  if (!email.trim()) {
    errors.push('Email is required')
  } else if (!emailRegex.test(email)) {
    errors.push('Please enter a valid email address')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export function validateUsername(username: string): ValidationResult {
  const errors: string[] = []

  if (!username.trim()) {
    errors.push('Username is required')
  } else if (username.length < 3) {
    errors.push('Username must be at least 3 characters')
  } else if (username.length > 30) {
    errors.push('Username must be less than 30 characters')
  } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.push('Username can only contain letters, numbers, and underscores')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export function validatePassword(password: string): ValidationResult {
  const errors: string[] = []

  if (!password) {
    errors.push('Password is required')
  } else {
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters')
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter')
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter')
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number')
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export function getPasswordStrength(password: string): {
  strength: 'weak' | 'medium' | 'strong'
  score: number
  feedback: string[]
} {
  let score = 0
  const feedback: string[] = []

  if (password.length >= 8) score++
  else feedback.push('Use at least 8 characters')

  if (/[A-Z]/.test(password)) score++
  else feedback.push('Add uppercase letters')

  if (/[a-z]/.test(password)) score++
  else feedback.push('Add lowercase letters')

  if (/[0-9]/.test(password)) score++
  else feedback.push('Add numbers')

  if (/[^A-Za-z0-9]/.test(password)) score++
  else feedback.push('Add special characters')

  if (password.length >= 12) score++

  let strength: 'weak' | 'medium' | 'strong'
  if (score <= 2) {
    strength = 'weak'
  } else if (score <= 4) {
    strength = 'medium'
  } else {
    strength = 'strong'
  }

  return { strength, score, feedback }
}

