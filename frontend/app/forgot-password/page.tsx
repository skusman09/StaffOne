'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { authAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import { validateEmail, validatePassword, getPasswordStrength } from '@/lib/validation'
import Link from 'next/link'
import { Mail, ArrowLeft, Loader2, CheckCircle2, ShieldCheck, Lock, Eye, EyeOff, KeyRound, AlertCircle } from 'lucide-react'

type Step = 'EMAIL' | 'OTP' | 'PASSWORD'

export default function ForgotPasswordPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('EMAIL')
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [passwordStrength, setPasswordStrength] = useState<{ strength: 'weak' | 'medium' | 'strong'; score: number } | null>(null)
  const [resendTimer, setResendTimer] = useState(0)
  
  const otpRefs = useRef<(HTMLInputElement | null)[]>([])

  // Resend timer logic
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer((prev) => prev - 1)
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [resendTimer])

  // Mutations
  const forgotPasswordMutation = useMutation({
    mutationFn: authAPI.forgotPassword,
    onSuccess: () => {
      setStep('OTP')
      setResendTimer(60)
      toast.success('Verification code sent to your email')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Something went wrong')
    },
  })

  const verifyOTPMutation = useMutation({
    mutationFn: (otpValue: string) => authAPI.verifyOTP(email, otpValue),
    onSuccess: () => {
      setStep('PASSWORD')
      toast.success('Code verified successfully')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Invalid verification code')
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: authAPI.resetPassword,
    onSuccess: () => {
      toast.success('Password reset successfully!')
      setTimeout(() => router.push('/login'), 2000)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to reset password')
    },
  })

  // Handlers
  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const validation = validateEmail(email)
    if (!validation.isValid) {
      setError(validation.errors[0])
      return
    }
    forgotPasswordMutation.mutate(email)
  }

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) value = value.slice(-1)
    if (!/^\d*$/.test(value)) return

    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)
    setError('')

    // Move to next input
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus()
    }

    // Auto-submit if all digits are entered
    const otpValue = newOtp.join('')
    if (otpValue.length === 6) {
      verifyOTPMutation.mutate(otpValue)
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus()
    }
  }

  const handleOtpSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const otpValue = otp.join('')
    if (otpValue.length !== 6) {
      setError('Please enter all 6 digits')
      return
    }
    verifyOTPMutation.mutate(otpValue)
  }

  const handleResendOtp = () => {
    if (resendTimer > 0) return
    forgotPasswordMutation.mutate(email)
  }

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const validation = validatePassword(password)
    if (!validation.isValid) {
      setError(validation.errors[0])
      return
    }

    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match')
      return
    }

    resetPasswordMutation.mutate({ 
      token: otp.join(''), 
      new_password: password 
    })
  }

  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(e.target.value)
    if (passwordError) setPasswordError('')
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setPassword(value)
    if (value) {
      const strength = getPasswordStrength(value)
      setPasswordStrength({ strength: strength.strength, score: strength.score })
    } else {
      setPasswordStrength(null)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 sm:p-10 space-y-8 border border-gray-100 dark:border-gray-700">
        
        {/* Step Header */}
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {step === 'EMAIL' && 'Forgot Password?'}
            {step === 'OTP' && 'Verify Email'}
            {step === 'PASSWORD' && 'Set New Password'}
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            {step === 'EMAIL' && "Enter your email and we'll send you a verification code."}
            {step === 'OTP' && `We've sent a 6-digit code to ${email}`}
            {step === 'PASSWORD' && 'Enter your new secure password below.'}
          </p>
        </div>


        {/* --- STEP 1: EMAIL --- */}
        {step === 'EMAIL' && (
          <form className="space-y-6" onSubmit={handleEmailSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-3 p-3 bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-xl text-sm text-red-600 dark:text-red-400 mb-4 transition-all duration-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <p className="font-medium text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={forgotPasswordMutation.isPending}
              className="w-full flex justify-center items-center py-3 px-4 rounded-lg shadow-sm text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-all"
            >
              {forgotPasswordMutation.isPending ? (
                <><Loader2 className="animate-spin mr-2 h-5 w-5" /> Sending...</>
              ) : 'Send Code'}
            </button>

            <div className="text-center">
              <Link href="/login" className="inline-flex items-center text-indigo-600 hover:text-indigo-500 text-sm font-medium">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to login
              </Link>
            </div>
          </form>
        )}

        {/* --- STEP 2: OTP --- */}
        {step === 'OTP' && (
          <form className="space-y-8" onSubmit={handleOtpSubmit}>
            <div className="flex justify-between gap-2 max-w-[280px] mx-auto">
              {otp.map((digit, idx) => (
                <input
                  key={idx}
                  ref={(el) => { otpRefs.current[idx] = el }}
                  type="text"
                  maxLength={1}
                  className="w-10 h-12 text-center text-xl font-bold border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                  value={digit}
                  onChange={(e) => handleOtpChange(idx, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(idx, e)}
                  autoFocus={idx === 0}
                />
              ))}
            </div>

            {error && (
              <div className="flex items-center gap-3 p-3 bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-xl text-sm text-red-600 dark:text-red-400 mb-4 transition-all duration-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <p className="font-medium">{error}</p>
              </div>
            )}

            <div className="text-center space-y-4">
              <button
                type="submit"
                disabled={verifyOTPMutation.isPending || otp.join('').length !== 6}
                className="w-full flex justify-center items-center py-3 px-4 rounded-lg shadow-sm text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-all font-premium"
              >
                {verifyOTPMutation.isPending ? (
                  <><Loader2 className="animate-spin mr-2 h-5 w-5" /> Verifying...</>
                ) : 'Continue'}
              </button>

              <div className="text-sm">
                <span className="text-gray-500 dark:text-gray-400">Didn't receive a code? </span>
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={resendTimer > 0 || forgotPasswordMutation.isPending}
                  className={`font-semibold transition-colors ${
                    resendTimer > 0 
                      ? 'text-gray-400 cursor-not-allowed' 
                      : 'text-indigo-600 hover:text-indigo-500'
                  }`}
                >
                  {resendTimer > 0 ? `Resend code in ${resendTimer}s` : 'Resend now'}
                </button>
              </div>
            </div>
          </form>
        )}

        {/* --- STEP 3: PASSWORD --- */}
        {step === 'PASSWORD' && (
          <form className="space-y-6" onSubmit={handlePasswordSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">New Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    className="block w-full pl-10 pr-10 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Enter new password"
                    value={password}
                    onChange={handlePasswordChange}
                  />
                  <button type="button" className="absolute inset-y-0 right-0 pr-3 flex items-center" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? <EyeOff className="h-5 w-5 text-gray-400" /> : <Eye className="h-5 w-5 text-gray-400" />}
                  </button>
                </div>
                {passwordStrength && (
                  <div className="mt-3 space-y-1.5">
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="text-gray-500 font-medium">Strength:</span>
                      <span className={`font-semibold ${
                        passwordStrength.strength === 'strong' ? 'text-green-500' : 
                        passwordStrength.strength === 'medium' ? 'text-yellow-500' : 'text-red-500'
                      }`}>
                        {passwordStrength.strength}
                      </span>
                    </div>
                    <div className="h-1.5 bg-gray-100 dark:bg-gray-700/50 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          passwordStrength.strength === 'strong' ? 'bg-green-500' : 
                          passwordStrength.strength === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                        }`} 
                        style={{ width: `${(passwordStrength.score/5)*100}%` }} 
                      />
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Confirm Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <ShieldCheck className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    className={`block w-full pl-10 pr-10 py-3 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all ${
                      passwordError ? 'border-red-300 dark:border-red-500 ring-1 ring-red-500/20' : 'border-gray-300 dark:border-gray-600'
                    }`}
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={handleConfirmPasswordChange}
                  />
                  <button 
                    type="button" 
                    className="absolute inset-y-0 right-0 pr-3 flex items-center" 
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff className="h-5 w-5 text-gray-400" /> : <Eye className="h-5 w-5 text-gray-400" />}
                  </button>
                </div>
                {passwordError && (
                  <p className="mt-1.5 text-xs font-semibold text-red-500 dark:text-red-400 ml-1">
                    {passwordError}
                  </p>
                )}
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-3 p-3 bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-xl text-sm text-red-600 dark:text-red-400 mb-4 transition-all duration-300">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <p className="font-medium text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={resetPasswordMutation.isPending}
              className="w-full flex justify-center items-center py-3 px-4 rounded-lg shadow-sm text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-all font-premium"
            >
              {resetPasswordMutation.isPending ? (
                <><Loader2 className="animate-spin mr-2 h-5 w-5" /> Resetting...</>
              ) : 'Reset Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
