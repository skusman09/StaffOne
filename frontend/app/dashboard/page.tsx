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
              <div className="card h-full bg-slate-900 border-slate-800 text-white">
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-indigo-500/10 rounded-lg">
                      <Clock className="w-5 h-5 text-indigo-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Today's Status</h2>
                  </div>
                  {todayStatus?.shift_type && (
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${SHIFT_TYPE_CONFIG[todayStatus.shift_type as ShiftType]?.bg || 'bg-slate-800'} ${SHIFT_TYPE_CONFIG[todayStatus.shift_type as ShiftType]?.color || 'text-slate-400'}`}>
                      {SHIFT_TYPE_CONFIG[todayStatus.shift_type as ShiftType]?.label || todayStatus.shift_type}
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Check-in</p>
                    <p className="text-xl font-mono font-bold">
                      {todayStatus?.check_in_time ? new Date(todayStatus.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
                    </p>
                  </div>
                  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Check-out</p>
                    <p className="text-xl font-mono font-bold">
                      {todayStatus?.check_out_time ? new Date(todayStatus.check_out_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
                    </p>
                  </div>
                </div>

                {todayStatus?.check_in_time && !todayStatus.check_out_time && (
                  <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-4 shadow-lg shadow-indigo-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs text-indigo-100 font-medium tracking-wide">LIVE DURATION</p>
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-300 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                      </span>
                    </div>
                    <p className="text-3xl font-mono font-bold tracking-tighter">{liveDuration || '00:00:00'}</p>
                  </div>
                )}

                {todayStatus?.check_out_time && todayStatus.hours_worked !== undefined && todayStatus.hours_worked > 0 && (
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
                    <p className="text-xs text-emerald-400 font-medium mb-1">TOTAL WORKED</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {todayStatus.hours_worked.toFixed(2)}<span className="text-sm font-normal ml-1 text-emerald-400/70">h</span>
                    </p>
                  </div>
                )}

                {!todayStatus?.check_in_time && (
                  <div className="flex flex-col items-center justify-center py-8 text-slate-500">
                    <Clock className="w-12 h-12 mb-2 opacity-20" />
                    <p className="text-sm">Ready to start your day?</p>
                  </div>
                )}
              </div>

              {/* Actions Card */}
              <div className="card h-full bg-slate-900 border-slate-800 text-white">
                <div className="flex items-center gap-2 mb-6">
                  <div className="p-2 bg-orange-500/10 rounded-lg">
                    <Zap className="w-5 h-5 text-orange-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Actions</h2>
                </div>

                {/* Check In Section */}
                {todayStatus?.can_check_in && (
                  <div className="space-y-4">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Select Shift Type</p>
                    <button
                      onClick={handleRegularCheckIn}
                      disabled={checkInMutation.isPending}
                      className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 py-4 px-6 rounded-xl font-bold flex items-center justify-center gap-3 transition-all active:scale-[0.98] shadow-lg shadow-indigo-600/20"
                    >
                      {checkInMutation.isPending ? (
                        <span className="spinner w-5 h-5" />
                      ) : (
                        <>
                          <Building2 className="w-5 h-5" />
                          <span>Regular Shift</span>
                        </>
                      )}
                    </button>

                    <div className="grid grid-cols-2 gap-3">
                      <button
                        onClick={handleBreakIn}
                        disabled={checkInMutation.isPending}
                        className="bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
                      >
                        <Clock className="w-4 h-4 text-slate-400" />
                        <span>Break</span>
                      </button>
                      <button
                        onClick={handleOvertimeCheckIn}
                        disabled={checkInMutation.isPending}
                        className="bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
                      >
                        <Zap className="w-4 h-4 text-slate-400" />
                        <span>Overtime</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Check Out Section */}
                {todayStatus?.can_check_out && (
                  <div className="space-y-4">
                    <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 mb-4">
                      <p className="text-xs text-rose-400 font-medium text-center">Active Shift: {SHIFT_TYPE_CONFIG[todayStatus?.shift_type as ShiftType]?.label || 'Regular'}</p>
                    </div>
                    <button
                      onClick={handleCheckOut}
                      disabled={checkOutMutation.isPending || statusLoading}
                      className="w-full bg-rose-600 hover:bg-rose-700 text-white py-4 rounded-xl font-bold text-lg active:scale-[0.98] transition-all shadow-lg shadow-rose-600/20"
                    >
                      {checkOutMutation.isPending ? 'CHECKING OUT...' : 'FINISH SHIFT'}
                    </button>
                    <p className="text-center text-xs text-slate-500">
                      Check out to submit your hours for today.
                    </p>
                  </div>
                )}

                {!todayStatus?.can_check_in && !todayStatus?.can_check_out && (
                  <div className="flex flex-col items-center justify-center py-10">
                    <div className="bg-emerald-500/20 p-3 rounded-full mb-3">
                      <ShieldCheck className="w-8 h-8 text-emerald-400" />
                    </div>
                    <p className="text-emerald-400 font-bold text-center">COMPLETED</p>
                    <p className="text-xs text-slate-500 mt-2">All tasks for this session are done.</p>
                  </div>
                )}
              </div>

              {/* Recent Effort Card */}
              <div className="card h-full bg-slate-900 border-slate-800 text-white">
                <div className="flex items-center gap-2 mb-6">
                  <div className="p-2 bg-blue-500/10 rounded-lg">
                    <Clock className="w-5 h-5 text-blue-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Recent Effort</h2>
                </div>

                {workingHours ? (
                  <div className="space-y-6">
                    <div className="bg-slate-950 border border-slate-800 rounded-2xl p-8 text-center">
                      <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-2">Total Hours (30d)</p>
                      <p className="text-5xl font-mono font-bold tracking-tighter">
                        {workingHours.total_hours.toFixed(1)}<span className="text-lg font-normal ml-1 text-indigo-400">h</span>
                      </p>
                    </div>

                    <div className="grid grid-cols-3 gap-1">
                      <div className="text-center">
                        <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Regular</p>
                        <p className="text-lg font-bold text-blue-400">{workingHours.regular_hours.toFixed(1)}h</p>
                      </div>
                      <div className="text-center border-x border-slate-800">
                        <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Overtime</p>
                        <p className="text-lg font-bold text-purple-400">{workingHours.overtime_hours.toFixed(1)}h</p>
                      </div>
                      <div className="text-center">
                        <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Break</p>
                        <p className="text-lg font-bold text-orange-400">{workingHours.break_hours?.toFixed(1) || '0.0'}h</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-center gap-2 text-slate-500 py-2 border-t border-slate-800">
                      <History className="w-3 h-3" />
                      <span className="text-[10px] font-bold uppercase tracking-widest">Based on {workingHours.records_count} records</span>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-slate-500 italic">
                    <p className="text-sm">No activity recorded yet.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Monthly Statistics Card */}
          {monthlyStats && (
            <div className="mt-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-indigo-500/10 rounded-lg">
                  <CalendarDays className="w-5 h-5 text-indigo-400" />
                </div>
                <h2 className="text-xl font-semibold text-white">Monthly Stats: {monthlyStats.month_name}</h2>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 transition-all hover:bg-slate-800/60">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Days Worked</p>
                  <p className="text-2xl font-bold text-white">{monthlyStats.days_worked}<span className="text-xs font-normal text-slate-500 ml-1">/{monthlyStats.working_days_in_month}</span></p>
                </div>
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 transition-all hover:bg-slate-800/60">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Absences</p>
                  <p className="text-2xl font-bold text-rose-400">{monthlyStats.days_absent}</p>
                </div>
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 transition-all hover:bg-slate-800/60">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Total Hours</p>
                  <p className="text-2xl font-bold text-white">{monthlyStats.total_hours}<span className="text-xs font-normal text-slate-500 ml-1">h</span></p>
                </div>
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 transition-all hover:bg-slate-800/60">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Overtime</p>
                  <p className="text-2xl font-bold text-amber-400">{monthlyStats.overtime_hours}<span className="text-xs font-normal text-slate-500 ml-1">h</span></p>
                </div>
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 transition-all hover:bg-slate-800/60">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Avg/Day</p>
                  <p className="text-2xl font-bold text-white">{monthlyStats.avg_hours_per_day}<span className="text-xs font-normal text-slate-500 ml-1">h</span></p>
                </div>
                <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 transition-all hover:bg-slate-800/60">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1">Attendance</p>
                  <p className="text-2xl font-bold text-emerald-400">{monthlyStats.attendance_percentage}<span className="text-xs font-normal text-slate-500 ml-1">%</span></p>
                </div>
              </div>
            </div>
          )}
          {/* Quick Links Section */}
          <div className="mt-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-indigo-500/10 rounded-lg">
                <LayoutDashboard className="w-5 h-5 text-indigo-400" />
              </div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Quick Access</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Link href="/history" className="group">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 transition-all hover:bg-slate-800 hover:-translate-y-1 active:scale-[0.98] shadow-lg border-l-4 border-l-blue-500">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-2 bg-blue-500/10 rounded-xl group-hover:bg-blue-500/20 transition-colors">
                      <History className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Review</div>
                  </div>
                  <h3 className="text-lg font-bold text-white mb-1">Attendance History</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">View your past check-in and check-out logs.</p>
                </div>
              </Link>

              <Link href="/leaves" className="group">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 transition-all hover:bg-slate-800 hover:-translate-y-1 active:scale-[0.98] shadow-lg border-l-4 border-l-orange-500">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-2 bg-orange-500/10 rounded-xl group-hover:bg-orange-500/20 transition-colors">
                      <CalendarDays className="w-6 h-6 text-orange-400" />
                    </div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Manage</div>
                  </div>
                  <h3 className="text-lg font-bold text-white mb-1">Leave Requests</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">Submit and track your time-off applications.</p>
                </div>
              </Link>

              {user?.role === 'admin' && (
                <Link href="/admin" className="group">
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 transition-all hover:bg-slate-800 hover:-translate-y-1 active:scale-[0.98] shadow-lg border-l-4 border-l-indigo-500">
                    <div className="flex items-center justify-between mb-4">
                      <div className="p-2 bg-indigo-500/10 rounded-xl group-hover:bg-indigo-500/20 transition-colors">
                        <ShieldCheck className="w-6 h-6 text-indigo-400" />
                      </div>
                      <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Admin</div>
                    </div>
                    <h3 className="text-lg font-bold text-white mb-1">Admin Panel</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">System management and employee analytics.</p>
                  </div>
                </Link>
              )}
            </div>
          </div>
        </div>
      </Container>
    </div>
  )
}
