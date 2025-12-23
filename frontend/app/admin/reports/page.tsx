'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { reportsAPI, adminAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'

interface UserSummary {
    user_id: number
    user_full_name: string
    user_email: string
    days_worked: number
    total_hours: number
    overtime_days: number
    overtime_hours: number
}

interface ReportResponse {
    start_date: string
    end_date: string
    total_users: number
    summaries: Record<number, UserSummary>
}

// Format date for display
const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    })
}

// Get default date range (start of month to today)
const getDefaultDateRange = () => {
    const today = new Date()
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    return {
        start: startOfMonth.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
    }
}

// Loading skeleton for table
function TableSkeleton() {
    return (
        <div className="animate-pulse">
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded mb-2"></div>
            ))}
        </div>
    )
}

export default function AdminReportsPage() {
    const router = useRouter()
    const [mounted, setMounted] = useState(false)

    // Filter state
    const defaultDates = getDefaultDateRange()
    const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
    const [startDate, setStartDate] = useState(defaultDates.start)
    const [endDate, setEndDate] = useState(defaultDates.end)

    useEffect(() => {
        setMounted(true)
    }, [])

    // Auth check
    const { data: user, isLoading: userLoading } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: mounted && isAuthenticated(),
    })

    // Redirect non-admin
    useEffect(() => {
        if (!mounted) return
        if (!isAuthenticated()) {
            router.push('/login')
            return
        }
        if (user && user.role !== 'admin') {
            router.push('/dashboard')
        }
    }, [router, mounted, user])

    // Fetch all users for dropdown
    const { data: allUsers } = useQuery({
        queryKey: ['all-users'],
        queryFn: () => adminAPI.getUsers(0, 200),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
    })

    // Fetch report data
    const {
        data: reportData,
        isLoading: reportLoading,
        error: reportError
    } = useQuery<ReportResponse>({
        queryKey: ['admin-report', selectedUserId, startDate, endDate],
        queryFn: () => reportsAPI.getAdminSummary(
            selectedUserId || undefined,
            startDate || undefined,
            endDate || undefined
        ),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
    })

    // Convert summaries object to array for rendering
    const summariesArray = reportData?.summaries
        ? Object.values(reportData.summaries)
        : []

    // Prevent hydration mismatch
    if (!mounted || userLoading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Navbar />
                <div className="mx-auto py-6 px-4 sm:px-6 lg:px-8 xl:px-12 max-w-full lg:max-w-7xl xl:max-w-[90vw] 2xl:max-w-[1800px]">
                    <div className="px-4 py-6 sm:px-0">
                        <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading...</div>
                    </div>
                </div>
            </div>
        )
    }

    // Non-admin redirect handled in useEffect, show nothing while redirecting
    if (user?.role !== 'admin') {
        return null
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <div className="mx-auto py-6 px-4 sm:px-6 lg:px-8 xl:px-12 max-w-full lg:max-w-7xl xl:max-w-[90vw] 2xl:max-w-[1800px]">
                <div className="px-4 py-6 sm:px-0">
                    {/* Header */}
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">📊 Admin Attendance Reports</h1>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            View aggregate attendance statistics for employees
                        </p>
                    </div>

                    {/* Filters Card */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">🔍 Filters</h2>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            {/* User Dropdown */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Employee
                                </label>
                                <select
                                    value={selectedUserId || ''}
                                    onChange={(e) => setSelectedUserId(e.target.value ? Number(e.target.value) : null)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                >
                                    <option value="">All Users</option>
                                    {allUsers?.map((user: any) => (
                                        <option key={user.id} value={user.id}>
                                            {user.full_name || user.username} (@{user.username})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Start Date */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Start Date
                                </label>
                                <input
                                    type="date"
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>

                            {/* End Date */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    End Date
                                </label>
                                <input
                                    type="date"
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                />
                            </div>

                            {/* Reset Button */}
                            <div className="flex items-end">
                                <button
                                    onClick={() => {
                                        const defaults = getDefaultDateRange()
                                        setSelectedUserId(null)
                                        setStartDate(defaults.start)
                                        setEndDate(defaults.end)
                                    }}
                                    className="px-4 py-2 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg text-sm font-medium transition-colors"
                                >
                                    Reset Filters
                                </button>
                            </div>
                        </div>

                        {/* Date range display */}
                        {reportData && (
                            <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                                Showing data from <span className="font-medium text-gray-700 dark:text-gray-300">{formatDate(reportData.start_date)}</span> to <span className="font-medium text-gray-700 dark:text-gray-300">{formatDate(reportData.end_date)}</span>
                            </div>
                        )}
                    </div>

                    {/* Summary Stats */}
                    {reportData && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-xl p-6 shadow-lg">
                                <p className="text-indigo-100 text-sm">Total Employees</p>
                                <p className="text-4xl font-bold">{reportData.total_users}</p>
                            </div>
                            <div className="bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-xl p-6 shadow-lg">
                                <p className="text-green-100 text-sm">Total Hours Worked</p>
                                <p className="text-4xl font-bold">
                                    {summariesArray.reduce((sum, s) => sum + s.total_hours, 0).toFixed(1)}h
                                </p>
                            </div>
                            <div className="bg-gradient-to-br from-orange-500 to-amber-600 text-white rounded-xl p-6 shadow-lg">
                                <p className="text-orange-100 text-sm">Total Overtime Hours</p>
                                <p className="text-4xl font-bold">
                                    {summariesArray.reduce((sum, s) => sum + s.overtime_hours, 0).toFixed(1)}h
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Results Table */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">📋 Attendance Summary</h2>
                            <button
                                onClick={() => reportsAPI.exportExcel(selectedUserId || undefined, startDate, endDate)}
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                Export Excel
                            </button>
                        </div>

                        {reportLoading ? (
                            <div className="p-6">
                                <TableSkeleton />
                            </div>
                        ) : reportError ? (
                            <div className="p-12 text-center">
                                <p className="text-red-500">Error loading report. Please try again.</p>
                            </div>
                        ) : summariesArray.length === 0 ? (
                            <div className="p-12 text-center">
                                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No records found</h3>
                                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                    No attendance data found for the selected filters.
                                </p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                    <thead className="bg-gray-50 dark:bg-gray-900">
                                        <tr>
                                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                User
                                            </th>
                                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                Days Worked
                                            </th>
                                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                Total Hours
                                            </th>
                                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                Overtime Days
                                            </th>
                                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                Overtime Hours
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                        {summariesArray.map((summary) => (
                                            <tr key={summary.user_id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        <div className="flex-shrink-0 h-10 w-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                                                            {summary.user_full_name.charAt(0).toUpperCase()}
                                                        </div>
                                                        <div className="ml-4">
                                                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                                {summary.user_full_name}
                                                            </div>
                                                            <div className="text-sm text-gray-500 dark:text-gray-400">
                                                                {summary.user_email}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                                                        {summary.days_worked} days
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                        {summary.total_hours.toFixed(2)} hrs
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                                    {summary.overtime_days > 0 ? (
                                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200">
                                                            {summary.overtime_days} days
                                                        </span>
                                                    ) : (
                                                        <span className="text-sm text-gray-400">0</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right">
                                                    {summary.overtime_hours > 0 ? (
                                                        <span className="text-sm font-medium text-orange-600 dark:text-orange-400">
                                                            +{summary.overtime_hours.toFixed(2)} hrs
                                                        </span>
                                                    ) : (
                                                        <span className="text-sm text-gray-400">0.00 hrs</span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div >
    )
}
