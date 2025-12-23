'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { attendanceAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { CalendarDays, ChevronLeft, ChevronRight, ChevronDown, Loader2 } from 'lucide-react'

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
                    <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 sm:px-0">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                        <div className="flex items-center gap-3">
                            <CalendarDays className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Attendance Calendar</h1>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Visual overview of your attendance
                        </p>
                    </div>

                    {/* Month/Year Selection */}
                    <div className="flex flex-wrap items-center justify-center sm:justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl mb-10">
                        <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1 shadow-inner">
                            <button
                                onClick={() => navigateMonth(-1)}
                                className="p-2.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all active:scale-95"
                                title="Previous Month"
                            >
                                <ChevronLeft className="w-5 h-5" />
                            </button>

                            <div className="h-6 w-px bg-slate-800 mx-1"></div>

                            <div className="flex gap-px px-1">
                                <div className="relative group">
                                    <select
                                        value={selectedMonth}
                                        onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                                        className="appearance-none bg-transparent hover:bg-slate-800 text-white text-base font-bold rounded-l-lg pl-4 pr-9 py-2.5 focus:outline-none focus:bg-slate-800 transition-all cursor-pointer"
                                    >
                                        {MONTH_NAMES.map((name, index) => (
                                            <option key={name} value={index} className="bg-slate-900 text-white font-sans">{name}</option>
                                        ))}
                                    </select>
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500 group-hover:text-indigo-400 transition-colors">
                                        <ChevronDown className="w-4 h-4" />
                                    </div>
                                </div>

                                <div className="relative group">
                                    <select
                                        value={selectedYear}
                                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                                        className="appearance-none bg-transparent hover:bg-slate-800 text-white text-base font-bold rounded-r-lg pl-4 pr-9 py-2.5 focus:outline-none focus:bg-slate-800 transition-all cursor-pointer border-l border-slate-800"
                                    >
                                        {Array.from({ length: 11 }, (_, i) => currentDate.getFullYear() - 5 + i).map(year => (
                                            <option key={year} value={year} className="bg-slate-900 text-white font-sans">{year}</option>
                                        ))}
                                    </select>
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500 group-hover:text-indigo-400 transition-colors">
                                        <ChevronDown className="w-4 h-4" />
                                    </div>
                                </div>
                            </div>

                            <div className="h-6 w-px bg-slate-800 mx-1"></div>

                            <button
                                onClick={() => navigateMonth(1)}
                                className="p-2.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-all active:scale-95"
                                title="Next Month"
                            >
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-500 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                            </span>
                            <p className="text-[10px] uppercase tracking-widest text-indigo-400 font-bold">Month View</p>
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                    <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-emerald-500 p-5 rounded-2xl shadow-lg hover:bg-slate-800/50 transition-colors">
                        <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Full Days</p>
                        <p className="text-3xl font-mono font-bold text-white">{stats.fullDays}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-amber-500 p-5 rounded-2xl shadow-lg hover:bg-slate-800/50 transition-colors">
                        <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Half Days</p>
                        <p className="text-3xl font-mono font-bold text-white">{stats.halfDays}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-rose-500 p-5 rounded-2xl shadow-lg hover:bg-slate-800/50 transition-colors">
                        <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Absent</p>
                        <p className="text-3xl font-mono font-bold text-white">{stats.absentDays}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-indigo-500 p-5 rounded-2xl shadow-lg hover:bg-slate-800/50 transition-colors">
                        <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Total Hours</p>
                        <p className="text-3xl font-mono font-bold text-white">{stats.totalHours.toFixed(1)}</p>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-blue-500 p-5 rounded-2xl shadow-lg hover:bg-slate-800/50 transition-colors">
                        <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Attendance</p>
                        <p className="text-3xl font-mono font-bold text-white">
                            {stats.workingDays > 0 ? Math.round(((stats.fullDays + stats.halfDays * 0.5) / stats.workingDays) * 100) : 0}%
                        </p>
                    </div>
                </div>

                {/* Calendar Grid */}
                <div className="bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
                    {/* Weekday Headers */}
                    <div className="grid grid-cols-7 bg-slate-950/80 border-b border-slate-800">
                        {WEEKDAYS.map(day => (
                            <div key={day} className="p-5 text-center text-[10px] uppercase tracking-[0.2em] font-black text-slate-500">
                                {day}
                            </div>
                        ))}
                    </div>

                    {/* Calendar Days */}
                    {isLoading ? (
                        <div className="p-32 text-center text-slate-500 italic">
                            <Loader2 className="w-10 h-10 animate-spin mx-auto mb-6 text-indigo-500/50" />
                            <p className="text-sm font-medium tracking-wide">Syncing attendance records...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-7">
                            {calendarDays.map((day, idx) => (
                                <div
                                    key={idx}
                                    className={`
                                        min-h-[120px] p-4 border-b border-r border-slate-800/40 transition-all duration-300
                                        ${!day.isCurrentMonth ? 'bg-slate-950/40 opacity-20 pointer-events-none' : 'hover:bg-indigo-500/5'}
                                        ${day.isToday ? 'bg-indigo-500/10 ring-2 ring-inset ring-indigo-500/30' : ''}
                                        ${day.isWeekend && day.isCurrentMonth ? 'bg-slate-950/20' : ''}
                                    `}
                                >
                                    {/* Date Number */}
                                    <div className="flex justify-between items-start mb-3">
                                        <span className={`
                                            w-9 h-9 flex items-center justify-center rounded-2xl text-base font-black shadow-lg transition-all transform
                                            ${day.isToday ? 'bg-indigo-600 text-white scale-110 shadow-indigo-500/40' : 'text-slate-500 group-hover:text-slate-300'}
                                        `}>
                                            {day.date.getDate()}
                                        </span>

                                        {/* Status Icon */}
                                        {day.isCurrentMonth && (
                                            <div className="flex items-center gap-1.5 pt-1">
                                                {day.status === 'full' && (
                                                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.7)]" title="Full Day" />
                                                )}
                                                {day.status === 'half' && (
                                                    <div className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_12px_rgba(245,158,11,0.7)]" title="Half Day" />
                                                )}
                                                {day.status === 'absent' && (
                                                    <div className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.7)]" title="Absent" />
                                                )}
                                                {day.isWeekend && (
                                                    <span className="text-[9px] font-black text-slate-700 uppercase tracking-tighter">Off</span>
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    {/* Hours Worked */}
                                    {day.isCurrentMonth && day.totalHours > 0 && (
                                        <div className="mt-auto pt-2 space-y-1.5">
                                            <p className="text-xl font-mono font-black text-white tracking-tighter leading-none">
                                                {day.totalHours.toFixed(1)}<span className="text-[10px] font-bold text-indigo-400 ml-0.5">H</span>
                                            </p>
                                            {day.records.length > 1 && (
                                                <div className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-indigo-500/10 text-[8px] font-black text-indigo-400 uppercase tracking-widest border border-indigo-500/20">
                                                    {day.records.length} SHIFTS
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Legend */}
                <div className="mt-10 flex flex-wrap items-center justify-center gap-8 px-6 py-4 bg-slate-900/50 rounded-2xl border border-slate-800/50">
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Full (8h+)</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"></div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Half (4-8h)</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]"></div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Absent</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="w-4 h-4 rounded border border-slate-700 bg-slate-950/40"></div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Weekend</span>
                    </div>
                </div>
            </Container>
        </div>
    )
}
