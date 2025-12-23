'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { payrollAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import {
    CircleDollarSign,
    BarChart3,
    Clock,
    Receipt,
    Filter,
    Loader2,
    AlertTriangle,
    Calendar
} from 'lucide-react'

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

export default function MySalaryPage() {
    const router = useRouter()
    const [mounted, setMounted] = useState(false)

    const currentDate = new Date()
    const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear())
    const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1)

    useEffect(() => {
        setMounted(true)
    }, [])

    const { data: user, isLoading: userLoading } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: mounted && isAuthenticated(),
    })

    useEffect(() => {
        if (!mounted) return
        if (!isAuthenticated()) {
            router.push('/login')
        }
    }, [router, mounted])

    const { data: salaryData, isLoading: salaryLoading, error: salaryError } = useQuery({
        queryKey: ['my-salary', selectedYear, selectedMonth],
        queryFn: () => payrollAPI.getMySalary(selectedYear, selectedMonth),
        enabled: mounted && isAuthenticated(),
        retry: false,
    })

    if (!mounted || userLoading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Navbar />
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                </div>
            </div>
        )
    }

    const yearOptions = Array.from({ length: 3 }, (_, i) => currentDate.getFullYear() - i)

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 py-6 sm:px-0">
                    {/* Header */}
                    <div className="mb-6">
                        <div className="flex items-center gap-3">
                            <CircleDollarSign className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">My Salary</h1>
                                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                    View your monthly salary breakdown and earnings
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Month/Year Selector */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 mb-6">
                        <div className="flex items-center gap-2 mb-2 text-indigo-600 dark:text-indigo-400">
                            <Filter className="w-4 h-4" />
                            <span className="text-sm font-medium">Filter Period</span>
                        </div>
                        <div className="flex flex-wrap gap-4 items-center">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Month</label>
                                <select
                                    value={selectedMonth}
                                    onChange={(e) => setSelectedMonth(Number(e.target.value))}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                >
                                    {MONTH_NAMES.map((name, i) => (
                                        <option key={i} value={i + 1}>{name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Year</label>
                                <select
                                    value={selectedYear}
                                    onChange={(e) => setSelectedYear(Number(e.target.value))}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                >
                                    {yearOptions.map((year) => (
                                        <option key={year} value={year}>{year}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Salary Details */}
                    {salaryLoading ? (
                        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-12 text-center">
                            <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-2" />
                            <div className="text-gray-500 dark:text-gray-400">Loading salary data...</div>
                        </div>
                    ) : salaryError ? (
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-8 text-center">
                            <AlertTriangle className="w-16 h-16 mx-auto text-yellow-400 mb-4" />
                            <h3 className="text-lg font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                                Salary Not Yet Generated
                            </h3>
                            <p className="text-yellow-700 dark:text-yellow-300 text-sm">
                                Your salary for {MONTH_NAMES[selectedMonth - 1]} {selectedYear} hasn't been generated yet.
                                <br />Please check back later or contact your administrator.
                            </p>
                        </div>
                    ) : salaryData ? (
                        <div className="space-y-6">
                            {/* Summary Card */}
                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl text-white relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
                                <div className="flex justify-between items-start mb-6">
                                    <div className="flex items-center gap-5">
                                        <div className="p-4 bg-indigo-500/10 rounded-2xl">
                                            <CircleDollarSign className="w-8 h-8 text-indigo-400" />
                                        </div>
                                        <div>
                                            <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Net Salary</p>
                                            <p className="text-5xl font-mono font-bold tracking-tighter text-white">₹{salaryData.net_salary?.toLocaleString() || '0'}</p>
                                        </div>
                                    </div>
                                    <span className={`px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-lg ${salaryData.status === 'paid' ? 'bg-emerald-500/20 text-emerald-400' :
                                        salaryData.status === 'approved' ? 'bg-blue-500/20 text-blue-400' :
                                            'bg-amber-500/20 text-amber-400'
                                        }`}>
                                        {salaryData.status || 'Draft'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Calendar className="w-3 h-3" />
                                    <p className="text-[10px] font-bold uppercase tracking-widest">
                                        {MONTH_NAMES[selectedMonth - 1]} {selectedYear}
                                    </p>
                                </div>
                            </div>

                            {/* Attendance Summary */}
                            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-indigo-500" />
                                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Attendance Summary</h2>
                                </div>
                                <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-100 dark:border-gray-600">
                                        <p className="text-gray-500 dark:text-gray-400 text-xs mb-1 uppercase tracking-wider font-semibold">Working Days</p>
                                        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{salaryData.office_working_days || 0}</p>
                                    </div>
                                    <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                        <p className="text-green-600 dark:text-green-400 text-xs mb-1">Days Worked</p>
                                        <p className="text-2xl font-bold text-green-700 dark:text-green-300">{salaryData.days_worked || 0}</p>
                                    </div>
                                    <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                                        <p className="text-red-600 dark:text-red-400 text-xs mb-1">Days Absent</p>
                                        <p className="text-2xl font-bold text-red-700 dark:text-red-300">{salaryData.days_absent || 0}</p>
                                    </div>
                                    <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                                        <p className="text-purple-600 dark:text-purple-400 text-xs mb-1">Overtime Days</p>
                                        <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{salaryData.overtime_days || 0}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Hours Breakdown */}
                            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <Clock className="w-5 h-5 text-indigo-500" />
                                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Hours Breakdown</h2>
                                </div>
                                <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                        <p className="text-blue-600 dark:text-blue-400 text-xs mb-1">Total Hours</p>
                                        <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{salaryData.total_hours_worked?.toFixed(1) || 0}h</p>
                                    </div>
                                    <div className="text-center p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                                        <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Expected Hours</p>
                                        <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">{salaryData.expected_hours?.toFixed(1) || 0}h</p>
                                    </div>
                                    <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                                        <p className="text-orange-600 dark:text-orange-400 text-xs mb-1">Overtime Hours</p>
                                        <p className="text-2xl font-bold text-orange-700 dark:text-orange-300">+{salaryData.overtime_hours?.toFixed(1) || 0}h</p>
                                    </div>
                                    <div className="text-center p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                                        <p className="text-indigo-600 dark:text-indigo-400 text-xs mb-1">Avg. Hours/Day</p>
                                        <p className="text-2xl font-bold text-indigo-700 dark:text-indigo-300">{salaryData.average_hours_per_day?.toFixed(1) || 0}h</p>
                                    </div>
                                </div>
                            </div>

                            {/* Salary Breakdown */}
                            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <Receipt className="w-5 h-5 text-indigo-500" />
                                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Salary Breakdown</h2>
                                </div>
                                <div className="p-6 space-y-4">
                                    <div className="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
                                        <span className="text-gray-600 dark:text-gray-400">Base Salary</span>
                                        <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">₹{salaryData.base_salary?.toLocaleString() || 0}</span>
                                    </div>
                                    <div className="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
                                        <span className="text-gray-600 dark:text-gray-400">Hourly Rate Used</span>
                                        <span className="text-gray-900 dark:text-gray-100">₹{salaryData.hourly_rate_used?.toFixed(2) || 0}/hr</span>
                                    </div>
                                    {salaryData.overtime_pay > 0 && (
                                        <div className="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
                                            <span className="text-green-600 dark:text-green-400">Overtime Pay</span>
                                            <span className="text-lg font-semibold text-green-600 dark:text-green-400">+₹{salaryData.overtime_pay?.toLocaleString() || 0}</span>
                                        </div>
                                    )}
                                    {(salaryData.deductions > 0 || salaryData.absence_deductions > 0) && (
                                        <div className="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
                                            <span className="text-red-600 dark:text-red-400">Deductions</span>
                                            <span className="text-lg font-semibold text-red-600 dark:text-red-400">-₹{((salaryData.deductions || 0) + (salaryData.absence_deductions || 0)).toLocaleString()}</span>
                                        </div>
                                    )}
                                    <div className="flex justify-between items-center py-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg px-4 mt-4">
                                        <span className="text-lg font-semibold text-indigo-900 dark:text-indigo-100">Net Salary</span>
                                        <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">₹{salaryData.net_salary?.toLocaleString() || 0}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Remarks */}
                            {salaryData.remarks && (
                                <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        <span className="font-medium">Note:</span> {salaryData.remarks}
                                    </p>
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            </Container>
        </div>
    )
}
