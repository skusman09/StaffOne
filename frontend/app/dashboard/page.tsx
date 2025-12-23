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
import Container from '@/components/Container'
import { Building2, Clock, Zap, History, CalendarDays, ShieldCheck, LayoutDashboard } from 'lucide-react'

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
  const [mounted, setMounted] = useState(false)
  const [sessionUser, setSessionUser] = useState<any>(null)
  const [selectedShiftType, setSelectedShiftType] = useState<ShiftType>(SHIFT_TYPES.REGULAR)

  // Real-time duration timer
  const [liveDuration, setLiveDuration] = useState<string>('')

  // Client-side only initialization
  useEffect(() => {
    setMounted(true)
    setSessionUser(getUser())
  }, [])

  useEffect(() => {
    if (!mounted) return

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
  }, [router, mounted])

  const { data: user, error: userError, isLoading: userLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authAPI.me,
    enabled: mounted && isAuthenticated(),
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
    enabled: mounted && isAuthenticated(),
    refetchOnWindowFocus: true,
  })

  const { data: workingHours } = useQuery({
    queryKey: ['workingHours'],
    queryFn: () => attendanceAPI.getWorkingHours(30),
    enabled: mounted && isAuthenticated(),
  })

  // Monthly statistics
  const currentDate = new Date()
  const { data: monthlyStats } = useQuery({
    queryKey: ['monthlyStats', currentDate.getFullYear(), currentDate.getMonth() + 1],
    queryFn: () => attendanceAPI.getMonthlyStats(currentDate.getFullYear(), currentDate.getMonth() + 1),
    enabled: mounted && isAuthenticated(),
  })

  // Real-time duration timer effect
  useEffect(() => {
    if (!todayStatus?.check_in_time || todayStatus?.check_out_time) {
      setLiveDuration('')
      return
    }

    const updateDuration = () => {
      const checkInTime = new Date(todayStatus.check_in_time).getTime()
      const now = Date.now()
      const diff = now - checkInTime

      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      const seconds = Math.floor((diff % (1000 * 60)) / 1000)

      setLiveDuration(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`)
    }

    updateDuration()
    const interval = setInterval(updateDuration, 1000)
    return () => clearInterval(interval)
  }, [todayStatus?.check_in_time, todayStatus?.check_out_time])

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

  // Prevent hydration mismatch - show loading until client-side mounted
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <Container className="py-6">
          <div className="px-4 py-6 sm:px-0">
            <DashboardSkeleton />
          </div>
        </Container>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <Container className="py-6">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex items-center gap-3 mb-6">
            <LayoutDashboard className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
          </div>

          {statusLoading ? (
            <DashboardSkeleton />
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Today's Status Card */}
              <div className="card">
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
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="relative flex h-3 w-3">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                            </span>
                            <span className="text-sm text-green-600 dark:text-green-400">Currently working</span>
                          </div>
                          {liveDuration && (
                            <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg p-4">
                              <p className="text-xs text-green-100 mb-1">Working Duration</p>
                              <p className="text-3xl font-mono font-bold tracking-wider">{liveDuration}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400">No check-in today</p>
                  )}
                </div>
              </div>

              {/* Actions Card */}
              <div className="card">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-4">Actions</h2>

                {/* Check In Section */}
                {todayStatus?.can_check_in && (
                  <div className="space-y-3">
                    <p className="text-sm text-slate-500 dark:text-slate-400">Select shift type:</p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={handleRegularCheckIn}
                        disabled={checkInMutation.isPending}
                        className="btn-primary btn-sm min-w-0"
                      >
                        {checkInMutation.isPending ? (
                          <span className="spinner" />
                        ) : (
                          <>
                            <Building2 className="w-4 h-4 flex-shrink-0" />
                            <span>Regular</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleBreakIn}
                        disabled={checkInMutation.isPending}
                        className="btn-primary btn-sm bg-amber-600 hover:bg-amber-700 min-w-0"
                      >
                        {checkInMutation.isPending ? (
                          <span className="spinner" />
                        ) : (
                          <>
                            <Clock className="w-4 h-4 flex-shrink-0" />
                            <span>Break</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleOvertimeCheckIn}
                        disabled={checkInMutation.isPending}
                        className="btn-primary btn-sm bg-purple-600 hover:bg-purple-700 min-w-0"
                      >
                        {checkInMutation.isPending ? (
                          <span className="spinner" />
                        ) : (
                          <>
                            <Zap className="w-4 h-4 flex-shrink-0" />
                            <span>Overtime</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Check Out Section - shown when user is checked in */}
                {todayStatus?.can_check_out && (
                  <div className="space-y-3 mt-4">
                    <button
                      onClick={handleCheckOut}
                      disabled={checkOutMutation.isPending || statusLoading}
                      className="btn-danger w-full"
                    >
                      {checkOutMutation.isPending ? 'Checking out...' : `Check Out (${SHIFT_TYPE_CONFIG[todayStatus?.shift_type as ShiftType]?.label || 'Shift'})`}
                    </button>

                    {todayStatus?.shift_type === 'regular' && (
                      <p className="text-xs text-slate-400 text-center">
                        Check out first, then start a break shift
                      </p>
                    )}
                  </div>
                )}

                {/* No action available message */}
                {!todayStatus?.can_check_in && !todayStatus?.can_check_out && (
                  <>
                    {todayStatus?.check_out_time ? (
                      <div className="text-center py-4">
                        <p className="text-green-600 dark:text-green-400 font-medium">✅ Shift completed!</p>
                        <p className="text-xs text-gray-400 mt-1">You can start a new shift anytime</p>
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        No actions available at this time.
                      </p>
                    )}
                  </>
                )}
              </div>

              {/* Working Hours Summary */}
              <div className="card">
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
          )}

          {/* Monthly Statistics Card */}
          {monthlyStats && (
            <div className="mt-6 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl p-6 shadow-lg">
              <h2 className="text-lg font-semibold mb-4">📅 {monthlyStats.month_name} {monthlyStats.year} Statistics</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-white/70 text-xs">Days Worked</p>
                  <p className="text-2xl font-bold">{monthlyStats.days_worked}<span className="text-sm font-normal text-white/70">/{monthlyStats.working_days_in_month}</span></p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-white/70 text-xs">Absences</p>
                  <p className="text-2xl font-bold text-red-300">{monthlyStats.days_absent}</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-white/70 text-xs">Total Hours</p>
                  <p className="text-2xl font-bold">{monthlyStats.total_hours}<span className="text-sm font-normal">h</span></p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-white/70 text-xs">Overtime</p>
                  <p className="text-2xl font-bold text-yellow-300">{monthlyStats.overtime_hours}<span className="text-sm font-normal">h</span></p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-white/70 text-xs">Avg/Day</p>
                  <p className="text-2xl font-bold">{monthlyStats.avg_hours_per_day}<span className="text-sm font-normal">h</span></p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-white/70 text-xs">Attendance</p>
                  <p className="text-2xl font-bold text-green-300">{monthlyStats.attendance_percentage}<span className="text-sm font-normal">%</span></p>
                </div>
              </div>
            </div>
          )}
          {/* Quick Links */}
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/history"
              className="btn-secondary"
            >
              <History className="w-4 h-4" />
              Attendance History
            </Link>
            <Link
              href="/leaves"
              className="btn-secondary"
            >
              <CalendarDays className="w-4 h-4" />
              Leave Requests
            </Link>
            {user?.role === 'admin' && (
              <Link
                href="/admin"
                className="btn-secondary"
              >
                <ShieldCheck className="w-4 h-4" />
                Admin Panel
              </Link>
            )}
          </div>
        </div>
      </Container>
    </div>
  )
}
