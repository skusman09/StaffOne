'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { adminAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import { TableSkeleton } from '@/components/LoadingSkeleton'
import { exportToCSV, formatDateForCSV } from '@/lib/export'
import { toast } from '@/lib/toast'
import Navbar from '@/components/Navbar'

type RoleFilter = 'all' | 'admin' | 'employee'

export default function AdminPage() {
  const router = useRouter()

  const authed = isAuthenticated()

  // Separate search states (prevents users search affecting attendance search)
  const [userSearchTerm, setUserSearchTerm] = useState('')
  const [attendanceSearchTerm, setAttendanceSearchTerm] = useState('')

  const [filterRole, setFilterRole] = useState<RoleFilter>('all')
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: '',
    end: '',
  })

  const [currentPage, setCurrentPage] = useState(1)
  const [attendancePage, setAttendancePage] = useState(1)
  const itemsPerPage = 10

  // Redirect unauth users
  useEffect(() => {
    if (!authed) router.push('/login')
  }, [authed, router])

  // Load current user
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authAPI.me,
    enabled: authed,
  })

  const isAdmin = authed && user?.role === 'admin'

  // Load admin data (only if admin)
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: () => adminAPI.getUsers(0, 100),
    enabled: isAdmin,
  })

  const { data: attendance, isLoading: attendanceLoading } = useQuery({
    queryKey: ['adminAttendance'],
    queryFn: () => adminAPI.getAttendance(0, 100),
    enabled: isAdmin,
  })

  // Redirect non-admin users
  useEffect(() => {
    if (authed && user && user.role !== 'admin') {
      router.push('/dashboard')
    }
  }, [authed, user, router])

  // Filters
  const filteredUsers = useMemo(() => {
    const list = Array.isArray(users) ? users : []
    const q = userSearchTerm.trim().toLowerCase()

    return list.filter((u: any) => {
      const matchesSearch =
        !q ||
        String(u.username ?? '').toLowerCase().includes(q) ||
        String(u.email ?? '').toLowerCase().includes(q) ||
        String(u.full_name ?? '').toLowerCase().includes(q)

      const matchesRole = filterRole === 'all' || u.role === filterRole
      return matchesSearch && matchesRole
    })
  }, [users, userSearchTerm, filterRole])

  const filteredAttendance = useMemo(() => {
    const list = Array.isArray(attendance) ? attendance : []
    const q = attendanceSearchTerm.trim().toLowerCase()

    const hasStart = Boolean(dateRange.start)
    const hasEnd = Boolean(dateRange.end)

    const startDate = hasStart ? new Date(dateRange.start) : null
    const endDate = hasEnd ? new Date(dateRange.end) : null
    if (endDate) endDate.setHours(23, 59, 59, 999)

    return list.filter((record: any) => {
      const username = String(record?.user?.username ?? '').toLowerCase()
      const email = String(record?.user?.email ?? '').toLowerCase()

      const matchesSearch = !q || username.includes(q) || email.includes(q)

      // Improved: supports start-only or end-only filtering too
      const checkInDate = new Date(record.check_in_time)
      if (hasStart && startDate && checkInDate < startDate) return false
      if (hasEnd && endDate && checkInDate > endDate) return false

      return matchesSearch
    })
  }, [attendance, attendanceSearchTerm, dateRange.start, dateRange.end])

  // Stats
  const todaysCheckins = useMemo(() => {
    const list = Array.isArray(attendance) ? attendance : []
    const today = new Date().toDateString()
    return list.filter((r: any) => new Date(r.check_in_time).toDateString() === today).length
  }, [attendance])

  // ✅ Return AFTER all hooks (prevents "Rendered more hooks" crash)
  if (!authed) return null
  if (userLoading) return <TableSkeleton rows={5} />
  if (!isAdmin) return null

  // Users pagination
  const totalUserPages = Math.max(1, Math.ceil(filteredUsers.length / itemsPerPage))
  const safeUserPage = Math.min(Math.max(currentPage, 1), totalUserPages)
  const paginatedUsers = filteredUsers.slice((safeUserPage - 1) * itemsPerPage, safeUserPage * itemsPerPage)

  // Attendance pagination
  const totalAttendancePages = Math.max(1, Math.ceil(filteredAttendance.length / itemsPerPage))
  const safeAttendancePage = Math.min(Math.max(attendancePage, 1), totalAttendancePages)
  const paginatedAttendance = filteredAttendance.slice(
    (safeAttendancePage - 1) * itemsPerPage,
    safeAttendancePage * itemsPerPage
  )

  const handleExportUsers = () => {
    try {
      exportToCSV(filteredUsers, 'users', {
        id: 'ID',
        username: 'Username',
        email: 'Email',
        full_name: 'Full Name',
        role: 'Role',
        is_active: 'Active',
        created_at: 'Created At',
      })
      toast.success('Users exported successfully!')
    } catch (error: any) {
      toast.error(error?.message || 'Failed to export users')
    }
  }

  const handleExportAttendance = () => {
    try {
      const exportData = filteredAttendance.map((record: any) => ({
        id: record.id,
        username: record.user?.username,
        email: record.user?.email,
        check_in_time: formatDateForCSV(record.check_in_time),
        check_out_time: record.check_out_time ? formatDateForCSV(record.check_out_time) : 'Pending',
        status: record.check_out_time ? 'Complete' : 'Pending',
      }))

      exportToCSV(exportData, 'attendance', {
        id: 'ID',
        username: 'Username',
        email: 'Email',
        check_in_time: 'Check-in Time',
        check_out_time: 'Check-out Time',
        status: 'Status',
      })
      toast.success('Attendance exported successfully!')
    } catch (error: any) {
      toast.error(error?.message || 'Failed to export attendance')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Admin Dashboard</h1>

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-8">
            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-gray-400 dark:text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                      />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Users</dt>
                      <dd className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {Array.isArray(users) ? users.length : 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-gray-400 dark:text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                      />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Records</dt>
                      <dd className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {Array.isArray(attendance) ? attendance.length : 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-6 w-6 text-gray-400 dark:text-gray-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Today's Check-ins</dt>
                      <dd className="text-lg font-semibold text-gray-900 dark:text-gray-100">{todaysCheckins}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Users Section */}
          <div className="mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-0">Users</h2>

              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Search users..."
                  value={userSearchTerm}
                  onChange={(e) => {
                    setUserSearchTerm(e.target.value)
                    setCurrentPage(1)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                />

                <select
                  value={filterRole}
                  onChange={(e) => {
                    setFilterRole(e.target.value as RoleFilter)
                    setCurrentPage(1)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="employee">Employee</option>
                </select>

                <button
                  onClick={handleExportUsers}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Export CSV
                </button>
              </div>
            </div>

            {usersLoading ? (
              <TableSkeleton rows={5} />
            ) : filteredUsers.length > 0 ? (
              <>
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {paginatedUsers.map((u: any) => (
                      <li key={u.id}>
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{u.username}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">{u.email}</p>
                              {u.full_name && <p className="text-sm text-gray-500 dark:text-gray-400">{u.full_name}</p>}
                            </div>

                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {u.role}
                            </span>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Users Pagination */}
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Page {safeUserPage} of {totalUserPages}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={safeUserPage <= 1}
                      className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-50"
                    >
                      Prev
                    </button>
                    <button
                      onClick={() => setCurrentPage((p) => Math.min(totalUserPages, p + 1))}
                      disabled={safeUserPage >= totalUserPages}
                      className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white shadow rounded-lg p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {userSearchTerm || filterRole !== 'all' ? 'Try adjusting your search or filters' : 'Get started by creating a new user'}
                </p>
              </div>
            )}
          </div>

          {/* Attendance Section */}
          <div>
            <div className="flex flex-col gap-4 mb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4 sm:mb-0">
                  All Attendance Records
                </h2>

                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    placeholder="Search attendance..."
                    value={attendanceSearchTerm}
                    onChange={(e) => {
                      setAttendanceSearchTerm(e.target.value)
                      setAttendancePage(1)
                    }}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm sm:w-64"
                  />

                  <button
                    onClick={handleExportAttendance}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Export CSV
                  </button>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => {
                    setDateRange({ ...dateRange, start: e.target.value })
                    setAttendancePage(1)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  placeholder="Start Date"
                />

                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => {
                    setDateRange({ ...dateRange, end: e.target.value })
                    setAttendancePage(1)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                  placeholder="End Date"
                />

                {(dateRange.start || dateRange.end) && (
                  <button
                    onClick={() => {
                      setDateRange({ start: '', end: '' })
                      setAttendancePage(1)
                    }}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
                  >
                    Clear Dates
                  </button>
                )}
              </div>
            </div>

            {attendanceLoading ? (
              <TableSkeleton rows={5} />
            ) : filteredAttendance.length > 0 ? (
              <>
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {paginatedAttendance.map((record: any) => (
                      <li key={record.id}>
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {record.user.username} ({record.user.email})
                              </p>
                              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                Check-in: {new Date(record.check_in_time).toLocaleString()}
                              </p>
                              {record.check_out_time && (
                                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                  Check-out: {new Date(record.check_out_time).toLocaleString()}
                                </p>
                              )}
                            </div>

                            <div className="ml-4">
                              {record.check_out_time ? (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Complete
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                  Pending
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Attendance Pagination */}
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Page {safeAttendancePage} of {totalAttendancePages}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAttendancePage((p) => Math.max(1, p - 1))}
                      disabled={safeAttendancePage <= 1}
                      className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-50"
                    >
                      Prev
                    </button>
                    <button
                      onClick={() => setAttendancePage((p) => Math.min(totalAttendancePages, p + 1))}
                      disabled={safeAttendancePage >= totalAttendancePages}
                      className="px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white shadow rounded-lg p-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No attendance records found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {attendanceSearchTerm ? 'Try adjusting your search' : 'Attendance records will appear here once users start checking in'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
