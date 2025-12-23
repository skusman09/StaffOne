'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { payrollAPI, adminAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { Banknote, RefreshCcw, FileText, Users, Wallet, TrendingUp, Landmark, ClipboardList, CheckCircle2, CreditCard, Loader2 } from 'lucide-react'

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

export default function PayrollPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)

    const currentDate = new Date()
    const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear())
    const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1)
    const [selectedUserId, setSelectedUserId] = useState<number | null>(null)

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
            return
        }
        if (user && user.role !== 'admin') {
            router.push('/dashboard')
        }
    }, [router, mounted, user])

    const { data: allUsers } = useQuery({
        queryKey: ['all-users'],
        queryFn: () => adminAPI.getUsers(0, 200),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
    })

    const { data: payrollData, isLoading: payrollLoading, error: payrollError } = useQuery({
        queryKey: ['payroll', selectedYear, selectedMonth],
        queryFn: () => payrollAPI.getPayroll(selectedYear, selectedMonth),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
        retry: false,
    })

    const generateMutation = useMutation({
        mutationFn: () => payrollAPI.generatePayroll(selectedYear, selectedMonth, selectedUserId || undefined),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['payroll'] })
        },
    })

    const approveMutation = useMutation({
        mutationFn: (recordId: number) => payrollAPI.approveSalary(recordId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['payroll'] })
        },
    })

    const exportPdfMutation = useMutation({
        mutationFn: () => payrollAPI.exportPdf(selectedYear, selectedMonth),
    })

    if (!mounted || userLoading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Navbar />
                <div className="flex items-center justify-center py-20">
                    <div className="text-gray-500 dark:text-gray-400">Loading...</div>
                </div>
            </div>
        )
    }

    if (user?.role !== 'admin') return null

    const yearOptions = Array.from({ length: 5 }, (_, i) => currentDate.getFullYear() - i)

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 py-6 sm:px-0">
                    {/* Header */}
                    <div className="mb-6">
                        <div className="flex items-center gap-3">
                            <Banknote className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Payroll Management</h1>
                        </div>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Generate and manage monthly salary records
                        </p>
                    </div>

                    {/* Controls */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6">
                        <div className="flex flex-wrap gap-4 items-end">
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
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Employee (Optional)</label>
                                <select
                                    value={selectedUserId || ''}
                                    onChange={(e) => setSelectedUserId(e.target.value ? Number(e.target.value) : null)}
                                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                >
                                    <option value="">All Employees</option>
                                    {allUsers?.map((u: any) => (
                                        <option key={u.id} value={u.id}>{u.full_name || u.username}</option>
                                    ))}
                                </select>
                            </div>
                            <button
                                onClick={() => generateMutation.mutate()}
                                disabled={generateMutation.isPending}
                                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                            >
                                {generateMutation.isPending ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <RefreshCcw className="w-4 h-4" />
                                )}
                                {generateMutation.isPending ? 'Generating...' : 'Generate Payroll'}
                            </button>
                            {payrollData && (
                                <button
                                    onClick={() => exportPdfMutation.mutate()}
                                    disabled={exportPdfMutation.isPending}
                                    className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                                >
                                    <FileText className="w-4 h-4" />
                                    {exportPdfMutation.isPending ? 'Exporting...' : 'Export PDF'}
                                </button>
                            )}
                        </div>
                        {generateMutation.isSuccess && (
                            <p className="mt-3 text-sm text-green-600 dark:text-green-400">✓ Payroll generated successfully!</p>
                        )}
                        {generateMutation.isError && (
                            <p className="mt-3 text-sm text-red-600 dark:text-red-400">Error generating payroll</p>
                        )}
                        {exportPdfMutation.isSuccess && (
                            <p className="mt-3 text-sm text-green-600 dark:text-green-400">✓ PDF downloaded!</p>
                        )}
                    </div>

                    {/* Summary Cards */}
                    {payrollData && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-blue-500 p-5 rounded-xl shadow-lg relative overflow-hidden">
                                <Users className="absolute -right-2 -bottom-2 w-20 h-20 text-white/5" />
                                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Total Employees</p>
                                <p className="text-3xl font-mono font-bold text-white">{payrollData.total_employees}</p>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-emerald-500 p-5 rounded-xl shadow-lg relative overflow-hidden">
                                <Wallet className="absolute -right-2 -bottom-2 w-20 h-20 text-white/5" />
                                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Total Base Salary</p>
                                <p className="text-3xl font-mono font-bold text-white">₹{payrollData.total_base_salary.toLocaleString()}</p>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-amber-500 p-5 rounded-xl shadow-lg relative overflow-hidden">
                                <TrendingUp className="absolute -right-2 -bottom-2 w-20 h-20 text-white/5" />
                                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Total Overtime Pay</p>
                                <p className="text-3xl font-mono font-bold text-white">+₹{payrollData.total_overtime_pay.toLocaleString()}</p>
                            </div>
                            <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-indigo-500 p-5 rounded-xl shadow-lg relative overflow-hidden">
                                <Landmark className="absolute -right-2 -bottom-2 w-20 h-20 text-white/5" />
                                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Total Net Salary</p>
                                <p className="text-3xl font-mono font-bold text-white">₹{payrollData.total_net_salary.toLocaleString()}</p>
                            </div>
                        </div>
                    )}

                    {/* Payroll Table */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                            <ClipboardList className="w-5 h-5 text-indigo-500" />
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                {MONTH_NAMES[selectedMonth - 1]} {selectedYear} Payroll
                            </h2>
                        </div>

                        {payrollLoading ? (
                            <div className="p-12 text-center text-gray-500">Loading payroll data...</div>
                        ) : payrollError ? (
                            <div className="p-12 text-center">
                                <p className="text-gray-500 dark:text-gray-400 mb-4">No payroll data found for this period.</p>
                                <button
                                    onClick={() => generateMutation.mutate()}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm"
                                >
                                    Generate Payroll Now
                                </button>
                            </div>
                        ) : payrollData?.records?.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                    <thead className="bg-gray-50 dark:bg-gray-900">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Employee</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Days</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Hours</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OT Hours</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Base Salary</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OT Pay</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Deductions</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Net Salary</th>
                                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                        {payrollData.records.map((record: any) => (
                                            <tr key={record.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                                <td className="px-4 py-3 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center text-indigo-700 dark:text-indigo-300 font-bold text-xs mr-3">
                                                            {(record.user_full_name || record.user_email).charAt(0).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                                {record.user_email.split('@')[0]}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm">
                                                    <span className="text-gray-900 dark:text-gray-100">{record.days_worked}</span>
                                                    <span className="text-gray-400">/{record.office_working_days}</span>
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm text-gray-900 dark:text-gray-100">
                                                    {record.total_hours_worked.toFixed(1)}h
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm">
                                                    {record.overtime_hours > 0 ? (
                                                        <span className="text-orange-600 dark:text-orange-400">+{record.overtime_hours.toFixed(1)}h</span>
                                                    ) : (
                                                        <span className="text-gray-400">0h</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm text-gray-900 dark:text-gray-100">
                                                    ₹{record.base_salary.toLocaleString()}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm">
                                                    {record.overtime_pay > 0 ? (
                                                        <span className="text-green-600 dark:text-green-400">+₹{record.overtime_pay.toLocaleString()}</span>
                                                    ) : (
                                                        <span className="text-gray-400">₹0</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm">
                                                    {(record.deductions + record.absence_deductions) > 0 ? (
                                                        <span className="text-red-600 dark:text-red-400">-₹{(record.deductions + record.absence_deductions).toLocaleString()}</span>
                                                    ) : (
                                                        <span className="text-gray-400">₹0</span>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-right text-sm font-semibold text-indigo-600 dark:text-indigo-400">
                                                    ₹{record.net_salary.toLocaleString()}
                                                </td>
                                                <td className="px-4 py-3 text-center">
                                                    {record.status === 'approved' ? (
                                                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 flex items-center justify-center gap-1">
                                                            <CheckCircle2 className="w-3 h-3" /> Approved
                                                        </span>
                                                    ) : record.status === 'paid' ? (
                                                        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 flex items-center justify-center gap-1">
                                                            <CreditCard className="w-3 h-3" /> Paid
                                                        </span>
                                                    ) : (
                                                        <button
                                                            onClick={() => approveMutation.mutate(record.id)}
                                                            disabled={approveMutation.isPending}
                                                            className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 hover:bg-yellow-200 dark:hover:bg-yellow-800"
                                                        >
                                                            Approve
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="p-12 text-center text-gray-500 dark:text-gray-400">
                                No payroll records found.
                            </div>
                        )}
                    </div>
                </div>
            </Container>
        </div>
    )
}
