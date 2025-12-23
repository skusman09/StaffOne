'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { attendanceAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

interface AttendanceRecord {
    id: number
    check_in_time: string
    check_out_time?: string
    hours_worked?: number
    shift_type: string
}

interface DayData {
    date: Date
    isCurrentMonth: boolean
    isToday: boolean
    isWeekend: boolean
    records: AttendanceRecord[]
    totalHours: number
    status: 'full' | 'half' | 'absent' | 'weekend' | 'none'
}

export default function CalendarPage() {
    const router = useRouter()
    const [mounted, setMounted] = useState(false)

    const currentDate = new Date()
    const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear())
    const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth())

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

    // Fetch attendance history for the selected month
    const startDate = new Date(selectedYear, selectedMonth, 1)
    const endDate = new Date(selectedYear, selectedMonth + 1, 0)

    const { data: historyData, isLoading } = useQuery({
        queryKey: ['calendar-history', selectedYear, selectedMonth],
        queryFn: () => attendanceAPI.getHistory(
            0,
            100,
            startDate.toISOString().split('T')[0],
            endDate.toISOString().split('T')[0]
        ),
        enabled: mounted && isAuthenticated(),
    })

    // Generate calendar grid
    const calendarDays = useMemo(() => {
        const days: DayData[] = []
        const firstDay = new Date(selectedYear, selectedMonth, 1)
        const lastDay = new Date(selectedYear, selectedMonth + 1, 0)
        const today = new Date()
        today.setHours(0, 0, 0, 0)

        // Get records map by date
        const recordsByDate: Record<string, AttendanceRecord[]> = {}
        if (historyData?.records) {
            for (const record of historyData.records) {
                const dateKey = new Date(record.check_in_time).toDateString()
                if (!recordsByDate[dateKey]) {
                    recordsByDate[dateKey] = []
                }
                recordsByDate[dateKey].push(record)
            }
        }

        // Add padding days from previous month
        const startPadding = firstDay.getDay()
        for (let i = startPadding - 1; i >= 0; i--) {
            const date = new Date(selectedYear, selectedMonth, -i)
            days.push({
                date,
                isCurrentMonth: false,
                isToday: false,
                isWeekend: date.getDay() === 0 || date.getDay() === 6,
                records: [],
                totalHours: 0,
                status: 'none'
            })
        }

        // Add days of current month
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(selectedYear, selectedMonth, day)
            date.setHours(0, 0, 0, 0)
            const dateKey = date.toDateString()
            const records = recordsByDate[dateKey] || []
            const totalHours = records.reduce((sum, r) => sum + (r.hours_worked || 0), 0)
            const isWeekend = date.getDay() === 0 || date.getDay() === 6
            const isPast = date < today

            let status: DayData['status'] = 'none'
            if (isWeekend) {
                status = 'weekend'
            } else if (records.length > 0) {
                status = totalHours >= 8 ? 'full' : totalHours >= 4 ? 'half' : 'absent'
            } else if (isPast && !isWeekend) {
                status = 'absent'
            }

            days.push({
                date,
                isCurrentMonth: true,
                isToday: date.getTime() === today.getTime(),
                isWeekend,
                records,
                totalHours,
                status
            })
        }

        // Add padding days for next month
        const endPadding = 42 - days.length
        for (let i = 1; i <= endPadding; i++) {
            const date = new Date(selectedYear, selectedMonth + 1, i)
            days.push({
                date,
                isCurrentMonth: false,
                isToday: false,
                isWeekend: date.getDay() === 0 || date.getDay() === 6,
                records: [],
                totalHours: 0,
                status: 'none'
            })
        }

        return days
    }, [selectedYear, selectedMonth, historyData])

    // Stats
    const stats = useMemo(() => {
        const currentMonthDays = calendarDays.filter(d => d.isCurrentMonth)
        const workingDays = currentMonthDays.filter(d => !d.isWeekend)
        const fullDays = workingDays.filter(d => d.status === 'full').length
        const halfDays = workingDays.filter(d => d.status === 'half').length
        const absentDays = workingDays.filter(d => d.status === 'absent' && d.date < new Date()).length
        const totalHours = currentMonthDays.reduce((sum, d) => sum + d.totalHours, 0)

        return { fullDays, halfDays, absentDays, totalHours, workingDays: workingDays.length }
    }, [calendarDays])

    const navigateMonth = (direction: number) => {
        const newDate = new Date(selectedYear, selectedMonth + direction, 1)
        setSelectedYear(newDate.getFullYear())
        setSelectedMonth(newDate.getMonth())
    }

    if (!mounted) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Navbar />
                <div className="flex items-center justify-center py-20">
                    <div className="text-gray-500">Loading...</div>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">📅 Attendance Calendar</h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Visual overview of your attendance
                        </p>
                    </div>

                    {/* Month Navigation */}
                    <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-xl p-2 shadow-sm">
                        <button
                            onClick={() => navigateMonth(-1)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                        </button>
                        <span className="px-4 py-2 text-lg font-semibold text-gray-900 dark:text-gray-100 min-w-[180px] text-center">
                            {MONTH_NAMES[selectedMonth]} {selectedYear}
                        </span>
                        <button
                            onClick={() => navigateMonth(1)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Full Days</p>
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.fullDays}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Half Days</p>
                        <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.halfDays}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Absent</p>
                        <p className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.absentDays}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Hours</p>
                        <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{stats.totalHours.toFixed(1)}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Attendance</p>
                        <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                            {stats.workingDays > 0 ? Math.round(((stats.fullDays + stats.halfDays * 0.5) / stats.workingDays) * 100) : 0}%
                        </p>
                    </div>
                </div>

                {/* Calendar Grid */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                    {/* Weekday Headers */}
                    <div className="grid grid-cols-7 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                        {WEEKDAYS.map(day => (
                            <div key={day} className="p-3 text-center text-sm font-semibold text-gray-600 dark:text-gray-400">
                                {day}
                            </div>
                        ))}
                    </div>

                    {/* Calendar Days */}
                    {isLoading ? (
                        <div className="p-12 text-center text-gray-500">Loading calendar...</div>
                    ) : (
                        <div className="grid grid-cols-7">
                            {calendarDays.map((day, idx) => (
                                <div
                                    key={idx}
                                    className={`
                                        min-h-[100px] p-2 border-b border-r border-gray-100 dark:border-gray-700/50
                                        ${!day.isCurrentMonth ? 'bg-gray-50 dark:bg-gray-800/50 opacity-50' : ''}
                                        ${day.isToday ? 'ring-2 ring-inset ring-indigo-500' : ''}
                                        ${day.isWeekend && day.isCurrentMonth ? 'bg-gray-50 dark:bg-gray-800/30' : ''}
                                    `}
                                >
                                    {/* Date Number */}
                                    <div className="flex justify-between items-start mb-1">
                                        <span className={`
                                            w-7 h-7 flex items-center justify-center rounded-full text-sm font-medium
                                            ${day.isToday ? 'bg-indigo-600 text-white' : 'text-gray-700 dark:text-gray-300'}
                                        `}>
                                            {day.date.getDate()}
                                        </span>

                                        {/* Status Badge */}
                                        {day.isCurrentMonth && (
                                            <span className={`
                                                px-1.5 py-0.5 text-[10px] font-medium rounded
                                                ${day.status === 'full' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : ''}
                                                ${day.status === 'half' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' : ''}
                                                ${day.status === 'absent' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : ''}
                                                ${day.status === 'weekend' ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400' : ''}
                                            `}>
                                                {day.status === 'full' && '✓'}
                                                {day.status === 'half' && '½'}
                                                {day.status === 'absent' && '✗'}
                                                {day.status === 'weekend' && 'Off'}
                                            </span>
                                        )}
                                    </div>

                                    {/* Hours Worked */}
                                    {day.isCurrentMonth && day.totalHours > 0 && (
                                        <div className="mt-1">
                                            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
                                                {day.totalHours.toFixed(1)}h
                                            </p>
                                            {day.records.length > 1 && (
                                                <p className="text-[10px] text-gray-400">
                                                    {day.records.length} shifts
                                                </p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Legend */}
                <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded bg-green-100 dark:bg-green-900/30"></span>
                        <span>Full Day (8+ hrs)</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded bg-yellow-100 dark:bg-yellow-900/30"></span>
                        <span>Half Day (4-8 hrs)</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded bg-red-100 dark:bg-red-900/30"></span>
                        <span>Absent</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded bg-gray-200 dark:bg-gray-700"></span>
                        <span>Weekend</span>
                    </div>
                </div>
            </Container>
        </div>
    )
}
