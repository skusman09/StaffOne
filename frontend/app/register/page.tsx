'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { authAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import { validateEmail, validateUsername, validatePassword, getPasswordStrength } from '@/lib/validation'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
  })
  const [errors, setErrors] = useState<{ email?: string; username?: string; password?: string }>({})
  const [passwordStrength, setPasswordStrength] = useState<{ strength: 'weak' | 'medium' | 'strong'; score: number } | null>(null)

  const registerMutation = useMutation({
    mutationFn: authAPI.register,
    onSuccess: () => {
      toast.success('Registration successful! Redirecting to login...')
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    },
    onError: (err: any) => {
      console.error('Registration error:', err)
      const errorMessage = err.response?.data?.detail || 
                          err.message || 
                          'Unable to connect to server. Please make sure the backend is running.'
      toast.error(errorMessage)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    
    // Validate all fields
    const emailValidation = validateEmail(formData.email)
    const usernameValidation = validateUsername(formData.username)
    const passwordValidation = validatePassword(formData.password)
    
    const newErrors: { email?: string; username?: string; password?: string } = {}
    
    if (!emailValidation.isValid) {
      newErrors.email = emailValidation.errors[0]
    }
    if (!usernameValidation.isValid) {
      newErrors.username = usernameValidation.errors[0]
    }
    if (!passwordValidation.isValid) {
      newErrors.password = passwordValidation.errors[0]
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }
    
    registerMutation.mutate(formData)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })
    
    // Clear error for this field
    if (errors[name as keyof typeof errors]) {
      setErrors({ ...errors, [name]: undefined })
    }
    
    // Update password strength indicator
    if (name === 'password') {
      if (value) {
        const strength = getPasswordStrength(value)
        setPasswordStrength({ strength: strength.strength, score: strength.score })
      } else {
        setPasswordStrength(null)
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Card Container */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 sm:p-10 space-y-8 border border-gray-100 dark:border-gray-700">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Create Account
            </h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Sign up to get started
            </p>
          </div>


          {/* Form */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                  </svg>
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className={`block w-full pl-10 pr-3 py-3 border rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-base ${
                    errors.email ? 'border-red-300 focus:ring-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? 'email-error' : undefined}
                />
              </div>
              {errors.email && (
                <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">
                  {errors.email}
                </p>
              )}
            </div>

            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-gray-700 mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className={`block w-full pl-10 pr-3 py-3 border rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-base ${
                    errors.username ? 'border-red-300 focus:ring-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={handleChange}
                  aria-invalid={!!errors.username}
                  aria-describedby={errors.username ? 'username-error' : undefined}
                />
              </div>
              {errors.username && (
                <p id="username-error" className="mt-1 text-sm text-red-600" role="alert">
                  {errors.username}
                </p>
              )}
            </div>

            {/* Full Name Field */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-semibold text-gray-700 mb-2">
                Full Name <span className="text-gray-400 font-normal">(Optional)</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-base"
                  placeholder="Enter your full name"
                  value={formData.full_name}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className={`block w-full pl-10 pr-3 py-3 border rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-base ${
                    errors.password ? 'border-red-300 focus:ring-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Create a password"
                  value={formData.password}
                  onChange={handleChange}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
              </div>
              {passwordStrength && formData.password && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-600">Password strength:</span>
                    <span className={`text-xs font-medium ${
                      passwordStrength.strength === 'strong' ? 'text-green-600' :
                      passwordStrength.strength === 'medium' ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {passwordStrength.strength.charAt(0).toUpperCase() + passwordStrength.strength.slice(1)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        passwordStrength.strength === 'strong' ? 'bg-green-500' :
                        passwordStrength.strength === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${(passwordStrength.score / 6) * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
              {errors.password && (
                <p id="password-error" className="mt-1 text-sm text-red-600" role="alert">
                  {errors.password}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={registerMutation.isPending}
                className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-base font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
              >
                {registerMutation.isPending ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Registering...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            </div>

            {/* Login Link */}
            <div className="text-center pt-4">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <Link href="/login" className="font-semibold text-indigo-600 hover:text-indigo-500 transition-colors duration-200">
                  Sign in here
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

