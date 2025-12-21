'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { attendanceAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'

export default function HistoryPage() {
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login')
    }
  }, [router])

  const { data: history, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => attendanceAPI.getHistory(0, 100),
    enabled: isAuthenticated(),
  })

  const { data: workingHours } = useQuery({
    queryKey: ['workingHours'],
    queryFn: () => attendanceAPI.getWorkingHours(30),
    enabled: isAuthenticated(),
  })

  if (!isAuthenticated()) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Attendance History</h1>

          {/* Summary Card */}
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
                            <p className="mt-1 text-xs text-indigo-500">📝 {record.admin_notes}</p>
                          )}
                        </div>
                        <div className="ml-4">
                          {record.check_out_time ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                              ✓ Complete
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">
                              ⏳ Active
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
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">No attendance records found</div>
          )}
        </div>
      </div>
    </div>
  )
}
