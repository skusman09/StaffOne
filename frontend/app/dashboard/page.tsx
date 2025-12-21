'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { attendanceAPI, authAPI, Cookies } from '@/lib/api'
import { isAuthenticated, getUser } from '@/lib/auth'
import { SessionManager } from '@/lib/session'
import { toast } from '@/lib/toast'
import { DashboardSkeleton } from '@/components/LoadingSkeleton'
import Navbar from '@/components/Navbar'
import Link from 'next/link'

// Shift type constants
const SHIFT_TYPES = {
  REGULAR: 'regular',
  BREAK: 'break',
  OVERTIME: 'overtime',
} as const

type ShiftType = typeof SHIFT_TYPES[keyof typeof SHIFT_TYPES]

// Shift type badge colors and labels
const SHIFT_TYPE_CONFIG: Record<ShiftType, { label: string; color: string; bg: string }> = {
  regular: { label: 'Regular', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900' },
  break: { label: 'Break', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900' },
  overtime: { label: 'Overtime', color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-100 dark:bg-purple-900' },
}

export default function DashboardPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [sessionUser, setSessionUser] = useState(getUser())
  const [selectedShiftType, setSelectedShiftType] = useState<ShiftType>(SHIFT_TYPES.REGULAR)

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login')
      return
    }

    const session = SessionManager.getSession()
    const token = Cookies.get('access_token')
    if (session?.user && session?.token === token) {
      setSessionUser(session.user)
    } else if (session && session.token !== token) {
      SessionManager.clearSession()
      setSessionUser(null)
    }
  }, [router])

  const { data: user, error: userError, isLoading: userLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authAPI.me,
    enabled: isAuthenticated(),
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
    staleTime: 5 * 60 * 1000,
    initialData: sessionUser || undefined,
  })

  useEffect(() => {
    if (user) {
      setSessionUser(user)
    }
  }, [user])

  useEffect(() => {
    if (userError && (userError as any).response?.status === 401) {
      console.error('[Dashboard] User query failed with 401:', userError)
    }
  }, [userError])

  const { data: todayStatus, isLoading: statusLoading, refetch: refetchTodayStatus } = useQuery({
    queryKey: ['todayStatus'],
    queryFn: attendanceAPI.getTodayStatus,
    enabled: isAuthenticated(),
    refetchOnWindowFocus: true,
  })

  const { data: workingHours } = useQuery({
    queryKey: ['workingHours'],
    queryFn: () => attendanceAPI.getWorkingHours(30),
    enabled: isAuthenticated(),
  })

  const checkInMutation = useMutation({
    mutationFn: attendanceAPI.checkIn,
    onSuccess: async () => {
      toast.success('Checked in successfully!')
      await queryClient.invalidateQueries({ queryKey: ['todayStatus'] })
      await queryClient.invalidateQueries({ queryKey: ['history'] })
      await queryClient.invalidateQueries({ queryKey: ['workingHours'] })
      await refetchTodayStatus()
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to check in')
    },
  })

  const checkOutMutation = useMutation({
    mutationFn: attendanceAPI.checkOut,
    onSuccess: async () => {
      toast.success('Checked out successfully!')
      await queryClient.invalidateQueries({ queryKey: ['todayStatus'] })
      await queryClient.invalidateQueries({ queryKey: ['history'] })
      await queryClient.invalidateQueries({ queryKey: ['workingHours'] })
      await refetchTodayStatus()
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to check out')
    },
  })

  const handleCheckIn = (shiftType: ShiftType = SHIFT_TYPES.REGULAR) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          checkInMutation.mutate({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            device_info: navigator.userAgent,
            shift_type: shiftType,
          })
        },
        () => {
          checkInMutation.mutate({ device_info: navigator.userAgent, shift_type: shiftType })
        }
      )
    } else {
      checkInMutation.mutate({ device_info: navigator.userAgent, shift_type: shiftType })
    }
  }

  const handleCheckOut = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          checkOutMutation.mutate({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            device_info: navigator.userAgent,
          })
        },
        () => {
          checkOutMutation.mutate({ device_info: navigator.userAgent })
        }
      )
    } else {
      checkOutMutation.mutate({ device_info: navigator.userAgent })
    }
  }

  // Convenience handlers for different shift types
  const handleRegularCheckIn = () => handleCheckIn(SHIFT_TYPES.REGULAR)
  const handleBreakIn = () => handleCheckIn(SHIFT_TYPES.BREAK)
  const handleOvertimeCheckIn = () => handleCheckIn(SHIFT_TYPES.OVERTIME)

  if (!isAuthenticated()) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Dashboard</h1>

          {statusLoading ? (
            <DashboardSkeleton />
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Today's Status Card */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Today's Status</h2>
                    {todayStatus?.shift_type && (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${SHIFT_TYPE_CONFIG[todayStatus.shift_type as ShiftType]?.bg || 'bg-gray-100'} ${SHIFT_TYPE_CONFIG[todayStatus.shift_type as ShiftType]?.color || 'text-gray-600'}`}>
                        {SHIFT_TYPE_CONFIG[todayStatus.shift_type as ShiftType]?.label || todayStatus.shift_type}
                      </span>
                    )}
                  </div>
                  {todayStatus?.check_in_time ? (
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">Check-in Time:</span>
                        <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                          {new Date(todayStatus.check_in_time).toLocaleTimeString()}
                        </p>
                      </div>
                      {todayStatus.check_out_time ? (
                        <>
                          <div>
                            <span className="text-sm text-gray-500 dark:text-gray-400">Check-out Time:</span>
                            <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                              {new Date(todayStatus.check_out_time).toLocaleTimeString()}
                            </p>
                          </div>
                          {todayStatus.hours_worked && (
                            <div>
                              <span className="text-sm text-gray-500 dark:text-gray-400">Hours Worked:</span>
                              <p className="text-lg font-medium text-green-600 dark:text-green-400">
                                {todayStatus.hours_worked.toFixed(2)} hours
                              </p>
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-yellow-600 dark:text-yellow-400">⏳ Still working...</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400">No check-in today</p>
                  )}
                </div>
              </div>

              {/* Actions Card */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Actions</h2>

                  {/* Check In Section */}
                  {todayStatus?.can_check_in && (
                    <div className="space-y-3 mb-4">
                      <p className="text-sm text-gray-500 dark:text-gray-400">Select shift type:</p>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          onClick={handleRegularCheckIn}
                          disabled={checkInMutation.isPending}
                          className="bg-blue-600 dark:bg-blue-700 text-white px-3 py-2 rounded-md text-xs font-medium hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {checkInMutation.isPending ? '...' : '🏢 Regular'}
                        </button>
                        <button
                          onClick={handleBreakIn}
                          disabled={checkInMutation.isPending}
                          className="bg-orange-600 dark:bg-orange-700 text-white px-3 py-2 rounded-md text-xs font-medium hover:bg-orange-700 dark:hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {checkInMutation.isPending ? '...' : '☕ Break'}
                        </button>
                        <button
                          onClick={handleOvertimeCheckIn}
                          disabled={checkInMutation.isPending}
                          className="bg-purple-600 dark:bg-purple-700 text-white px-3 py-2 rounded-md text-xs font-medium hover:bg-purple-700 dark:hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {checkInMutation.isPending ? '...' : '⏰ Overtime'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Check Out Section - shown when user is checked in */}
                  {todayStatus?.can_check_out && (
                    <div className="space-y-3">
                      <button
                        onClick={handleCheckOut}
                        disabled={checkOutMutation.isPending || statusLoading}
                        className="w-full bg-red-600 dark:bg-red-700 text-white px-4 py-3 rounded-md text-sm font-medium hover:bg-red-700 dark:hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {checkOutMutation.isPending ? 'Checking out...' : `🔴 Check Out (${SHIFT_TYPE_CONFIG[todayStatus?.shift_type as ShiftType]?.label || 'Shift'})`}
                      </button>

                      {/* Quick Break Toggle - when on regular shift, allow starting a break */}
                      {todayStatus?.shift_type === 'regular' && (
                        <p className="text-xs text-gray-400 text-center">
                          Check out first, then start a break shift
                        </p>
                      )}
                    </div>
                  )}

                  {/* Already checked out message */}
                  {!todayStatus?.can_check_in && !todayStatus?.can_check_out && todayStatus?.check_out_time && (
                    <div className="text-center py-4">
                      <p className="text-green-600 dark:text-green-400 font-medium">✅ Shift completed!</p>
                      <p className="text-xs text-gray-400 mt-1">You can start a new shift anytime</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Working Hours Summary */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Last 30 Days</h2>
                  {workingHours ? (
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm text-gray-500 dark:text-gray-400">Total Hours:</span>
                        <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                          {workingHours.total_hours.toFixed(1)}h
                        </p>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Regular:</span>
                          <p className="font-medium text-blue-600 dark:text-blue-400">{workingHours.regular_hours.toFixed(1)}h</p>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Overtime:</span>
                          <p className="font-medium text-purple-600 dark:text-purple-400">{workingHours.overtime_hours.toFixed(1)}h</p>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Break:</span>
                          <p className="font-medium text-orange-600 dark:text-orange-400">{workingHours.break_hours?.toFixed(1) || '0.0'}h</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-400">{workingHours.records_count} records</p>
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400">No data yet</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Quick Links */}
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/history"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 dark:text-indigo-300 bg-indigo-100 dark:bg-indigo-900 hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
            >
              📋 Attendance History
            </Link>
            <Link
              href="/leaves"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-900 hover:bg-purple-200 dark:hover:bg-purple-800 transition-colors"
            >
              🏖️ Leave Requests
            </Link>
            {user?.role === 'admin' && (
              <Link
                href="/admin"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900 hover:bg-red-200 dark:hover:bg-red-800 transition-colors"
              >
                ⚙️ Admin Panel
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
