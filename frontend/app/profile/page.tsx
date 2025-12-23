'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authAPI } from '@/lib/api'
import { getFullAvatarUrl } from '@/lib/utils'
import { isAuthenticated } from '@/lib/auth'
import { toast } from '@/lib/toast'
import { validateEmail, validatePassword } from '@/lib/validation'
import { DashboardSkeleton } from '@/components/LoadingSkeleton'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { Camera, Loader2, Eye, EyeOff } from 'lucide-react'

export default function ProfilePage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [mounted, setMounted] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
  })
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const [errors, setErrors] = useState<{ [key: string]: string }>({})
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    if (!isAuthenticated()) {
      router.push('/login')
    }
  }, [router, mounted])

  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authAPI.me,
    enabled: mounted && isAuthenticated(),
  })

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || '',
        username: user.username || '',
        full_name: user.full_name || '',
      })
    }
  }, [user])

  const updateProfileMutation = useMutation({
    mutationFn: async (data: { email: string; username: string; full_name?: string }) => {
      return authAPI.updateProfile(data)
    },
    onSuccess: () => {
      toast.success('Profile updated successfully!')
      setIsEditing(false)
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.detail || err.message || 'Failed to update profile'
      toast.error(message)
    },
  })

  const changePasswordMutation = useMutation({
    mutationFn: async (data: { currentPassword: string; newPassword: string }) => {
      return authAPI.changePassword({
        current_password: data.currentPassword,
        new_password: data.newPassword
      })
    },
    onSuccess: () => {
      toast.success('Password changed successfully! Redirecting to login...')
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      // Logout and redirect after 2 seconds
      setTimeout(() => {
        authAPI.logout()
        router.push('/login')
      }, 2000)
    },
    onError: (err: any) => {
      const message = err.response?.data?.detail || err.message || 'Failed to change password'
      toast.error(message)
    },
  })

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    const emailValidation = validateEmail(formData.email)
    if (!emailValidation.isValid) {
      setErrors({ email: emailValidation.errors[0] })
      return
    }

    updateProfileMutation.mutate(formData)
  }

  const uploadAvatarMutation = useMutation({
    mutationFn: async (file: File) => {
      return authAPI.uploadAvatar(file)
    },
    onSuccess: () => {
      toast.success('Avatar updated successfully!')
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
    onError: (err: any) => {
      const message = err.response?.data?.detail || err.message || 'Failed to upload avatar'
      toast.error(message)
    },
  })

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadAvatarMutation.mutate(file)
    }
  }

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (!passwordData.currentPassword) {
      setErrors({ currentPassword: 'Current password is required' })
      return
    }

    const passwordValidation = validatePassword(passwordData.newPassword)
    if (!passwordValidation.isValid) {
      setErrors({ newPassword: passwordValidation.errors[0] })
      return
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setErrors({ confirmPassword: 'Passwords do not match' })
      return
    }

    changePasswordMutation.mutate({
      currentPassword: passwordData.currentPassword,
      newPassword: passwordData.newPassword,
    })
  }

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <DashboardSkeleton />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <DashboardSkeleton />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <Container className="py-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-6">Profile Settings</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Profile Information */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Profile Information</h2>
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-primary"
                >
                  Edit Profile
                </button>
              )}
            </div>

            {/* Avatar Section */}
            <div className="mb-8 flex flex-col items-center">
              <div className="relative group">
                <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-white dark:border-gray-700 shadow-lg bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center text-4xl font-bold text-indigo-600 dark:text-indigo-300">
                  {user?.avatar_url ? (
                    <img
                      src={getFullAvatarUrl(user.avatar_url) || undefined}
                      alt={user?.username || 'User'}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    user?.username?.charAt(0).toUpperCase()
                  )}
                </div>
                <label className="absolute bottom-0 right-0 p-2 bg-indigo-600 rounded-full text-white cursor-pointer shadow-md hover:bg-indigo-700 transition-colors">
                  <input
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    disabled={uploadAvatarMutation.isPending}
                  />
                  {uploadAvatarMutation.isPending ? (
                    <Loader2 className="animate-spin h-5 w-5" />
                  ) : (
                    <Camera className="w-5 h-5" />
                  )}
                </label>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">Click the camera icon to update your photo</p>
            </div>

            {isEditing ? (
              <form onSubmit={handleProfileSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.email ? 'border-red-300' : 'border-gray-300 dark:border-gray-600'
                      }`}
                  />
                  {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    disabled
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Username cannot be changed</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.full_name || ''}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={updateProfileMutation.isPending}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium disabled:opacity-50 transition-colors"
                  >
                    {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false)
                      setErrors({})
                      if (user) {
                        setFormData({
                          email: user.email || '',
                          username: user.username || '',
                          full_name: user.full_name || '',
                        })
                      }
                    }}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Email:</span>
                  <p className="text-gray-900 dark:text-gray-100">{user?.email}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Username:</span>
                  <p className="text-gray-900 dark:text-gray-100">{user?.username}</p>
                </div>
                {user?.full_name && (
                  <div>
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Full Name:</span>
                    <p className="text-gray-900 dark:text-gray-100">{user.full_name}</p>
                  </div>
                )}
                <div>
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Role:</span>
                  <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user?.role === 'admin'
                    ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                    : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                    }`}>
                    {user?.role}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Change Password */}
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Change Password</h2>
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Current Password
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.current ? 'text' : 'password'}
                    value={passwordData.currentPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                    className={`w-full px-3 py-2 pr-10 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.currentPassword ? 'border-red-300' : 'border-gray-300 dark:border-gray-600'}`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showPasswords.current ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {errors.currentPassword && <p className="mt-1 text-sm text-red-600">{errors.currentPassword}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  New Password
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.new ? 'text' : 'password'}
                    value={passwordData.newPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                    className={`w-full px-3 py-2 pr-10 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.newPassword ? 'border-red-300' : 'border-gray-300 dark:border-gray-600'}`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showPasswords.new ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {errors.newPassword && <p className="mt-1 text-sm text-red-600">{errors.newPassword}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Confirm New Password
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.confirm ? 'text' : 'password'}
                    value={passwordData.confirmPassword}
                    onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                    className={`w-full px-3 py-2 pr-10 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${errors.confirmPassword ? 'border-red-300' : 'border-gray-300 dark:border-gray-600'}`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showPasswords.confirm ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>}
              </div>

              <button
                type="submit"
                disabled={changePasswordMutation.isPending}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium disabled:opacity-50 transition-colors"
              >
                {changePasswordMutation.isPending ? 'Changing...' : 'Change Password'}
              </button>
            </form>
          </div>
        </div>
      </Container>
    </div>
  )
}
