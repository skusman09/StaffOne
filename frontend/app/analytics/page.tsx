'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { analyticsAPI, authAPI, adminAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import {
    BarChart3,
    Users,
    CalendarOff,
    TrendingUp,
    Trophy,
    Calendar,
    Clock,
    Zap,
    AlertCircle,
    Loader2
} from 'lucide-react'

// Simple bar chart component (no external dependencies)
function SimpleBarChart({ data, dataKey, labelKey, color = '#6366f1' }: {
    data: any[]
    dataKey: string
    labelKey: string
    color?: string
}) {
    if (!data || data.length === 0) return <div className="text-gray-500 text-center py-4">No data</div>

    const maxValue = Math.max(...data.map(d => d[dataKey] || 0))

    return (
        <div className="space-y-2">
            {data.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-20 truncate">{item[labelKey]?.split('-').pop() || item[labelKey]}</span>
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                                width: `${maxValue > 0 ? (item[dataKey] / maxValue) * 100 : 0}%`,
                                backgroundColor: color
                            }}
                        />
                    </div>
                    <span className="text-xs font-medium w-12 text-right">{item[dataKey]?.toFixed?.(1) || item[dataKey]}</span>
                </div>
            ))}
        </div>
    )
}

export default function AnalyticsPage() {
    const router = useRouter()
    const [days, setDays] = useState(7)
    const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null)

    useEffect(() => {
        if (!isAuthenticated()) {
            router.push('/login')
        }
    }, [router])

    const { data: user } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: isAuthenticated(),
    })

    const isAdmin = user?.role === 'admin'

    const { data: dashboard, isLoading } = useQuery({
        queryKey: ['analytics-dashboard', days],
        queryFn: () => analyticsAPI.getDashboard(days),
        enabled: isAuthenticated() && isAdmin,
    })

    const { data: myStats } = useQuery({
        queryKey: ['my-stats', days],
        queryFn: () => analyticsAPI.getMyStats(days),
        enabled: isAuthenticated(),
    })

    // Get all users for employee selector (admin only)
    const { data: allUsers } = useQuery({
        queryKey: ['all-users'],
        queryFn: () => adminAPI.getUsers(0, 200),
        enabled: isAuthenticated() && isAdmin,
    })

    // Get selected employee's stats (admin only)
    const { data: selectedEmployeeStats, isLoading: employeeStatsLoading } = useQuery({
        queryKey: ['employee-stats', selectedEmployeeId, days],
        queryFn: () => analyticsAPI.getUserStats(selectedEmployeeId!, days),
        enabled: isAuthenticated() && isAdmin && selectedEmployeeId !== null,
    })

    const selectedEmployee = allUsers?.find((u: any) => u.id === selectedEmployeeId)

    if (!isAuthenticated()) return null

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 py-6 sm:px-0">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-3">
                            <BarChart3 className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
                        </div>
                        <select
                            value={days}
                            onChange={(e) => setDays(Number(e.target.value))}
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                            <option value={7}>Last 7 days</option>
                            <option value={14}>Last 14 days</option>
                            <option value={30}>Last 30 days</option>
                            <option value={90}>Last 90 days</option>
                        </select>
                    </div>

                    {/* My Stats */}
                    {myStats && (
                        <div className="mb-8">
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">My Performance</h2>
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Total Hours</p>
                                    <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{myStats.total_hours}h</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Daily</p>
                                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">{myStats.avg_daily_hours}h</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Overtime</p>
                                    <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{myStats.overtime_hours}h</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Days Worked</p>
                                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{myStats.total_records}</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
                                    <p className="text-2xl font-bold text-red-600 dark:text-red-400">{myStats.pending_checkouts}</p>
                                </div>
                            </div>

                            {/* Daily breakdown chart */}
                            {myStats.daily_breakdown && myStats.daily_breakdown.length > 0 && (
                                <div className="mt-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Daily Hours</h3>
                                    <SimpleBarChart data={myStats.daily_breakdown} dataKey="hours" labelKey="date" color="#6366f1" />
                                </div>
                            )}
                        </div>
                    )}

                    {/* Admin Dashboard */}
                    {isAdmin && dashboard && (
                        <>
                            {/* Today's Overview */}
                            <div className="mb-8">
                                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Today's Overview</h2>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg shadow-lg">
                                        <p className="text-green-100 text-sm">Check-ins</p>
                                        <p className="text-4xl font-bold">{dashboard.today_checkins}</p>
                                    </div>
                                    <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg shadow-lg">
                                        <p className="text-blue-100 text-sm">Check-outs</p>
                                        <p className="text-4xl font-bold">{dashboard.today_checkouts}</p>
                                    </div>
                                    <div className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white p-6 rounded-lg shadow-lg">
                                        <p className="text-yellow-100 text-sm">Still Working</p>
                                        <p className="text-4xl font-bold">{dashboard.today_pending}</p>
                                    </div>
                                    <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg shadow-lg">
                                        <p className="text-purple-100 text-sm">On Leave</p>
                                        <p className="text-4xl font-bold">{dashboard.today_on_leave}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Employee Stats */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                                        <Users className="w-5 h-5 text-indigo-500" />
                                        <span>Employees</span>
                                    </h3>
                                    <div className="flex items-center gap-8">
                                        <div>
                                            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{dashboard.total_employees}</p>
                                            <p className="text-sm text-gray-500">Total</p>
                                        </div>
                                        <div>
                                            <p className="text-3xl font-bold text-green-600">{dashboard.active_employees}</p>
                                            <p className="text-sm text-gray-500">Active</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                                        <CalendarOff className="w-5 h-5 text-orange-500" />
                                        <span>Leave Breakdown</span>
                                    </h3>
                                    {dashboard.leave_breakdown && dashboard.leave_breakdown.length > 0 ? (
                                        <div className="space-y-2">
                                            {dashboard.leave_breakdown.map((item: any) => (
                                                <div key={item.leave_type} className="flex justify-between items-center">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{item.leave_type}</span>
                                                    <span className="text-sm font-medium">{item.count} ({item.total_days} days)</span>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-gray-500">No leaves in this period</p>
                                    )}
                                </div>
                            </div>

                            {/* Attendance Trends */}
                            {dashboard.daily_stats && dashboard.daily_stats.length > 0 && (
                                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-8">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5 text-green-500" />
                                        <span>Attendance Trends</span>
                                    </h3>
                                    <SimpleBarChart data={dashboard.daily_stats} dataKey="total_checkins" labelKey="date" color="#10b981" />
                                </div>
                            )}

                            {/* Top Performers */}
                            {dashboard.top_performers && dashboard.top_performers.length > 0 && (
                                <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                                        <Trophy className="w-5 h-5 text-yellow-500" />
                                        <span>Top Performers</span>
                                    </h3>
                                    <div className="overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                            <thead>
                                                <tr>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                                                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                                                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Hours</th>
                                                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Avg/Day</th>
                                                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Days</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                                {dashboard.top_performers.map((user: any, i: number) => (
                                                    <tr key={user.user_id} className={i === 0 ? 'bg-yellow-50 dark:bg-yellow-900/20' : ''}>
                                                        <td className="px-4 py-3 text-sm">
                                                            {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                                                        </td>
                                                        <td className="px-4 py-3">
                                                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                                {user.full_name || user.username}
                                                            </div>
                                                            <div className="text-xs text-gray-500">@{user.username}</div>
                                                        </td>
                                                        <td className="px-4 py-3 text-right text-sm font-medium text-indigo-600">{user.total_hours}h</td>
                                                        <td className="px-4 py-3 text-right text-sm">{user.avg_hours}h</td>
                                                        <td className="px-4 py-3 text-right text-sm">{user.total_days}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </>
                    )}

                    {/* Individual Employee Stats (Admin) */}
                    {isAdmin && allUsers && allUsers.length > 0 && (
                        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-8">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">👤 Individual Employee Performance</h3>
                            <div className="flex flex-wrap gap-4 mb-4">
                                <select
                                    value={selectedEmployeeId || ''}
                                    onChange={(e) => setSelectedEmployeeId(e.target.value ? Number(e.target.value) : null)}
                                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                >
                                    <option value="">Select an employee...</option>
                                    {allUsers.map((user: any) => (
                                        <option key={user.id} value={user.id}>
                                            {user.full_name || user.username} (@{user.username})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {selectedEmployeeId && (
                                <div>
                                    {employeeStatsLoading ? (
                                        <div className="text-center py-4 text-gray-500">Loading employee stats...</div>
                                    ) : selectedEmployeeStats ? (
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-2 mb-4">
                                                <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                                                    {selectedEmployee?.full_name || selectedEmployee?.username}
                                                </span>
                                                <span className="text-sm text-gray-500">@{selectedEmployee?.username}</span>
                                            </div>
                                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                                                    <p className="text-sm text-gray-500 dark:text-gray-400">Total Hours</p>
                                                    <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{selectedEmployeeStats.total_hours}h</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                                                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Daily</p>
                                                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">{selectedEmployeeStats.avg_daily_hours}h</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                                                    <p className="text-sm text-gray-500 dark:text-gray-400">Overtime</p>
                                                    <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{selectedEmployeeStats.overtime_hours}h</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                                                    <p className="text-sm text-gray-500 dark:text-gray-400">Days Worked</p>
                                                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{selectedEmployeeStats.total_records}</p>
                                                </div>
                                                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                                                    <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
                                                    <p className="text-2xl font-bold text-red-600 dark:text-red-400">{selectedEmployeeStats.pending_checkouts}</p>
                                                </div>
                                            </div>
                                            {/* Daily breakdown for selected employee */}
                                            {selectedEmployeeStats.daily_breakdown && selectedEmployeeStats.daily_breakdown.length > 0 && (
                                                <div className="mt-4">
                                                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Daily Hours</h4>
                                                    <SimpleBarChart data={selectedEmployeeStats.daily_breakdown} dataKey="hours" labelKey="date" color="#8b5cf6" />
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-gray-500">No data available for this employee</p>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Non-admin message */}
                    {!isAdmin && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mt-6">
                            <p className="text-blue-700 dark:text-blue-300">
                                📊 Team-wide analytics are only visible to administrators.
                            </p>
                        </div>
                    )}

                    {isLoading && (
                        <div className="text-center py-12 text-gray-500">Loading analytics...</div>
                    )}
                </div>
            </Container>
        </div>
    )
}
