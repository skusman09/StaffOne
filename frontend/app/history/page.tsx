'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { attendanceAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { Calendar, Clock, Search, CheckCircle2, Loader2, AlertCircle, FileText, History } from 'lucide-react'

export default function HistoryPage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  // Date range filter state
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  // Monthly stats state
  const currentDate = new Date()
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear())
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    if (!isAuthenticated()) {
      router.push('/login')
    }
  }, [router, mounted])

  const { data: history, isLoading, refetch } = useQuery({
    queryKey: ['history', startDate, endDate],
    queryFn: () => attendanceAPI.getHistory(0, 100, startDate || undefined, endDate || undefined),
    enabled: mounted && isAuthenticated(),
  })

  const { data: workingHours } = useQuery({
    queryKey: ['workingHours'],
    queryFn: () => attendanceAPI.getWorkingHours(30),
    enabled: mounted && isAuthenticated(),
  })

  const { data: monthlyStats, isLoading: monthlyLoading } = useQuery({
    queryKey: ['monthlyStats', selectedYear, selectedMonth],
    queryFn: () => attendanceAPI.getMonthlyStats(selectedYear, selectedMonth),
    enabled: mounted && isAuthenticated(),
  })

  const handleFilter = () => {
    refetch()
  }

  const handleClearFilter = () => {
    setStartDate('')
    setEndDate('')
  }

  // Generate year options (last 5 years)
  const yearOptions = Array.from({ length: 5 }, (_, i) => currentDate.getFullYear() - i)
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <Container className="py-6">
          <div className="px-4 py-6 sm:px-0">
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading...</div>
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
            <History className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Attendance History</h1>
          </div>

          {/* Monthly Statistics Card */}
          <div className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl p-6 mb-6 shadow-lg">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
              <div className="flex items-center gap-2 mb-3 md:mb-0">
                <Calendar className="w-5 h-5" />
                <h2 className="text-lg font-semibold">Monthly Statistics</h2>
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(Number(e.target.value))}
                  className="px-3 py-1.5 rounded-lg bg-white/20 border border-white/30 text-white text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
                >
                  {monthNames.map((name, i) => (
                    <option key={i} value={i + 1} className="text-gray-900">{name}</option>
                  ))}
                </select>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(Number(e.target.value))}
                  className="px-3 py-1.5 rounded-lg bg-white/20 border border-white/30 text-white text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
                >
                  {yearOptions.map((year) => (
                    <option key={year} value={year} className="text-gray-900">{year}</option>
                  ))}
                </select>
              </div>
            </div>

            {monthlyLoading ? (
              <div className="text-center py-4 text-white/70">Loading monthly stats...</div>
            ) : monthlyStats ? (
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
            ) : (
              <div className="text-center py-4 text-white/70">No data available</div>
            )}
          </div>

          {/* Summary Card (Last 30 Days) */}
          {workingHours && (
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg p-6 mb-6 shadow-lg">
              <h2 className="text-lg font-medium mb-3">Last 30 Days Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-indigo-200 text-sm">Total Hours</p>
                  <p className="text-3xl font-bold">{workingHours.total_hours.toFixed(1)}h</p>
                </div>
                <div>
                  <p className="text-indigo-200 text-sm">Regular</p>
                  <p className="text-2xl font-semibold">{workingHours.regular_hours.toFixed(1)}h</p>
                </div>
                <div>
                  <p className="text-indigo-200 text-sm">Overtime</p>
                  <p className="text-2xl font-semibold text-yellow-300">{workingHours.overtime_hours.toFixed(1)}h</p>
                </div>
                <div>
                  <p className="text-indigo-200 text-sm">Records</p>
                  <p className="text-2xl font-semibold">{workingHours.records_count}</p>
                </div>
              </div>
            </div>
          )}

          {/* Date Range Filter */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-6 shadow">
            <div className="flex items-center gap-2 mb-3 ">
              <Search className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter by Date Range</h3>
            </div>
            <div className="flex flex-wrap gap-3 items-end">
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                />
              </div>
              <button
                onClick={handleFilter}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm font-medium transition-colors"
              >
                Apply Filter
              </button>
              {(startDate || endDate) && (
                <button
                  onClick={handleClearFilter}
                  className="px-4 py-2 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-md text-sm font-medium transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            {(startDate || endDate) && (
              <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-2">
                Showing records {startDate && `from ${startDate}`} {endDate && `to ${endDate}`}
              </p>
            )}
          </div>

          {/* History List */}
          {isLoading ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading...</div>
          ) : history && history.length > 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                {history.map((record: any) => (
                  <li key={record.id}>
                    <div className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400">
                              {new Date(record.check_in_time).toLocaleDateString('en-US', {
                                weekday: 'short',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })}
                            </p>
                            {record.shift_type && record.shift_type !== 'regular' && (
                              <span className="px-2 py-0.5 text-xs rounded bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                                {record.shift_type.toUpperCase()}
                              </span>
                            )}
                          </div>
                          <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-500 dark:text-gray-400">
                            <div>
                              <span className="text-gray-400">In:</span>{' '}
                              <span className="text-gray-700 dark:text-gray-300">
                                {new Date(record.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">Out:</span>{' '}
                              <span className="text-gray-700 dark:text-gray-300">
                                {record.check_out_time
                                  ? new Date(record.check_out_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                  : '-'}
                              </span>
                            </div>
                            {record.hours_worked !== null && (
                              <div>
                                <span className="text-gray-400">Hours:</span>{' '}
                                <span className="text-green-600 dark:text-green-400 font-medium">
                                  {record.hours_worked.toFixed(2)}h
                                </span>
                              </div>
                            )}
                            {record.is_auto_checkout && (
                              <span className="text-xs text-orange-500">Auto-closed</span>
                            )}
                          </div>
                          {!record.is_location_valid && (
                            <p className="mt-1 text-xs text-red-500">⚠️ Location flagged: {record.location_flag_reason}</p>
                          )}
                          {record.admin_notes && (
                            <p className="mt-1 text-xs text-indigo-500 flex items-center gap-1">
                              <FileText className="w-3 h-3" /> {record.admin_notes}
                            </p>
                          )}
                        </div>
                        <div className="ml-4">
                          {record.check_out_time ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              Complete
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 gap-1">
                              <Clock className="w-3 h-3" />
                              Active
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              {startDate || endDate ? 'No records found for the selected date range' : 'No attendance records found'}
            </div>
          )}
        </div>
      </Container>
    </div>
  )
}
