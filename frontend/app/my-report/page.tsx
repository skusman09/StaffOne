'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { payrollAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'

// Get default date range (start of month to today)
const getDefaultDateRange = () => {
    const today = new Date()
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
    return {
        start: startOfMonth.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
    }
}

const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    })
}

export default function MyReportPage() {
    const router = useRouter()
    const [mounted, setMounted] = useState(false)

    const defaultDates = getDefaultDateRange()
    const [startDate, setStartDate] = useState(defaultDates.start)
    const [endDate, setEndDate] = useState(defaultDates.end)

    useEffect(() => {
        setMounted(true)
    }, [])

    useEffect(() => {
        if (!mounted) return
        if (!isAuthenticated()) {
            router.push('/login')
        }
    }, [router, mounted])

    const { data: user } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: mounted && isAuthenticated(),
    })

    const { data: report, isLoading, error } = useQuery({
        queryKey: ['my-attendance-report', startDate, endDate],
        queryFn: () => payrollAPI.getMyAttendance(startDate, endDate),
        enabled: mounted && isAuthenticated() && !!startDate && !!endDate,
    })

    if (!mounted) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Navbar />
                <div className="flex items-center justify-center py-20">
                    <div className="text-gray-500 dark:text-gray-400">Loading...</div>
                </div>
            </div>
        )
    }

    const metrics = report?.metrics

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 py-6 sm:px-0">
                    {/* Header */}
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">📊 My Attendance Report</h1>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            View your attendance metrics and hours breakdown
                        </p>
                    </div>

                    {/* Date Range Filter */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6">
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">📅 Select Period</h2>
                        <div className="flex flex-wrap gap-4 items-end">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Start Date
                                </label>
                                <input
                                    type="date"
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    End Date
                                </label>
                                <input
                                    type="date"
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                            <button
                                onClick={() => {
                                    const defaults = getDefaultDateRange()
                                    setStartDate(defaults.start)
                                    setEndDate(defaults.end)
                                }}
                                className="px-4 py-2 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg text-sm font-medium transition-colors"
                            >
                                Reset to This Month
                            </button>
                        </div>
                    </div>

                    {isLoading ? (
                        <div className="text-center py-12 text-gray-500">Loading report...</div>
                    ) : error ? (
                        <div className="text-center py-12 text-red-500">Error loading report. Please try again.</div>
                    ) : metrics ? (
                        <>
                            {/* Overview Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                                <div className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-xl p-6 shadow-lg">
                                    <p className="text-blue-100 text-sm">Days Worked</p>
                                    <p className="text-4xl font-bold">
                                        {metrics.days_worked}
                                        <span className="text-lg font-normal text-blue-200">/ {metrics.office_working_days}</span>
                                    </p>
                                    <p className="text-sm text-blue-200 mt-1">{metrics.days_absent} absent days</p>
                                </div>
                                <div className="bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-xl p-6 shadow-lg">
                                    <p className="text-green-100 text-sm">Total Hours Worked</p>
                                    <p className="text-4xl font-bold">{metrics.total_hours_worked.toFixed(1)}h</p>
                                    <p className="text-sm text-green-200 mt-1">Expected: {metrics.expected_hours.toFixed(1)}h</p>
                                </div>
                                <div className="bg-gradient-to-br from-purple-500 to-violet-600 text-white rounded-xl p-6 shadow-lg">
                                    <p className="text-purple-100 text-sm">Average Hours/Day</p>
                                    <p className="text-4xl font-bold">{metrics.average_hours_per_day.toFixed(1)}h</p>
                                    <p className="text-sm text-purple-200 mt-1">Standard: 9h</p>
                                </div>
                            </div>

                            {/* Detailed Metrics */}
                            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                        📋 Detailed Metrics
                                        <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
                                            ({formatDate(report.period_start)} - {formatDate(report.period_end)})
                                        </span>
                                    </h2>
                                </div>
                                <div className="p-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                        {/* Working Days */}
                                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">📆 Working Days</h3>
                                            <div className="space-y-2">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Office Working Days</span>
                                                    <span className="font-semibold text-gray-900 dark:text-gray-100">{metrics.office_working_days}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Days Worked</span>
                                                    <span className="font-semibold text-green-600 dark:text-green-400">{metrics.days_worked}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Days Absent</span>
                                                    <span className="font-semibold text-red-600 dark:text-red-400">{metrics.days_absent}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Hours */}
                                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">⏱️ Hours</h3>
                                            <div className="space-y-2">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Total Worked</span>
                                                    <span className="font-semibold text-gray-900 dark:text-gray-100">{metrics.total_hours_worked.toFixed(2)}h</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Expected</span>
                                                    <span className="font-semibold text-gray-500">{metrics.expected_hours.toFixed(2)}h</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Average/Day</span>
                                                    <span className="font-semibold text-blue-600 dark:text-blue-400">{metrics.average_hours_per_day.toFixed(2)}h</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Overtime */}
                                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">⚡ Overtime</h3>
                                            <div className="space-y-2">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Overtime Days</span>
                                                    <span className="font-semibold text-orange-600 dark:text-orange-400">{metrics.overtime_days}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Overtime Hours</span>
                                                    <span className="font-semibold text-orange-600 dark:text-orange-400">+{metrics.overtime_hours.toFixed(2)}h</span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Undertime */}
                                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                                            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">⚠️ Undertime</h3>
                                            <div className="space-y-2">
                                                <div className="flex justify-between">
                                                    <span className="text-gray-600 dark:text-gray-300">Undertime Hours</span>
                                                    <span className="font-semibold text-red-600 dark:text-red-400">-{metrics.undertime_hours.toFixed(2)}h</span>
                                                </div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                                    Hours below 9h/day standard
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                            No attendance data found for the selected period.
                        </div>
                    )}
                </div>
            </Container>
        </div>
    )
}
