'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leaveAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import { toast } from '@/lib/toast'
import Navbar from '@/components/Navbar'

const LEAVE_TYPES = [
    { value: 'annual', label: '🏖️ Annual Leave' },
    { value: 'sick', label: '🤒 Sick Leave' },
    { value: 'casual', label: '📅 Casual Leave' },
    { value: 'unpaid', label: '💰 Unpaid Leave' },
    { value: 'maternity', label: '👶 Maternity Leave' },
    { value: 'paternity', label: '👨‍👧 Paternity Leave' },
    { value: 'bereavement', label: '🕊️ Bereavement Leave' },
    { value: 'other', label: '📝 Other' },
]

const STATUS_COLORS: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

export default function LeavesPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({
        leave_type: 'annual',
        start_date: '',
        end_date: '',
        reason: '',
    })

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

    const { data: leaves, isLoading } = useQuery({
        queryKey: ['myLeaves'],
        queryFn: () => leaveAPI.getMyLeaves(0, 100),
        enabled: isAuthenticated(),
    })

    const { data: stats } = useQuery({
        queryKey: ['leaveStats'],
        queryFn: leaveAPI.getStats,
        enabled: isAuthenticated(),
    })

    const createMutation = useMutation({
        mutationFn: leaveAPI.create,
        onSuccess: () => {
            toast.success('Leave request submitted!')
            queryClient.invalidateQueries({ queryKey: ['myLeaves'] })
            queryClient.invalidateQueries({ queryKey: ['leaveStats'] })
            setShowForm(false)
            setFormData({ leave_type: 'annual', start_date: '', end_date: '', reason: '' })
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.detail || 'Failed to submit leave request')
        },
    })

    const cancelMutation = useMutation({
        mutationFn: leaveAPI.cancel,
        onSuccess: () => {
            toast.success('Leave request cancelled')
            queryClient.invalidateQueries({ queryKey: ['myLeaves'] })
            queryClient.invalidateQueries({ queryKey: ['leaveStats'] })
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.detail || 'Failed to cancel leave')
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        createMutation.mutate(formData)
    }

    if (!isAuthenticated()) return null

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Leave Management</h1>
                        <button
                            onClick={() => setShowForm(!showForm)}
                            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                            {showForm ? 'Cancel' : '+ Request Leave'}
                        </button>
                    </div>

                    {/* Stats Cards */}
                    {stats && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                <p className="text-sm text-gray-500 dark:text-gray-400">Leaves Taken</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total_leaves_taken}</p>
                            </div>
                            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                <p className="text-sm text-gray-500 dark:text-gray-400">Days Used</p>
                                <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{stats.total_days_taken}</p>
                            </div>
                            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
                                <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.pending_requests}</p>
                            </div>
                            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                                <p className="text-sm text-gray-500 dark:text-gray-400">Approved (Year)</p>
                                <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.approved_this_year}</p>
                            </div>
                        </div>
                    )}

                    {/* Request Form */}
                    {showForm && (
                        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-6">
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">New Leave Request</h2>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Leave Type</label>
                                        <select
                                            value={formData.leave_type}
                                            onChange={(e) => setFormData({ ...formData, leave_type: e.target.value })}
                                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        >
                                            {LEAVE_TYPES.map((type) => (
                                                <option key={type.value} value={type.value}>{type.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
                                        <input
                                            type="date"
                                            value={formData.start_date}
                                            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                            required
                                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
                                        <input
                                            type="date"
                                            value={formData.end_date}
                                            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                            required
                                            min={formData.start_date}
                                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Reason (Optional)</label>
                                    <textarea
                                        value={formData.reason}
                                        onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                                        rows={3}
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                        placeholder="Reason for leave..."
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={createMutation.isPending}
                                    className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
                                >
                                    {createMutation.isPending ? 'Submitting...' : 'Submit Request'}
                                </button>
                            </form>
                        </div>
                    )}

                    {/* Leave List */}
                    <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">My Leave Requests</h2>
                        </div>
                        {isLoading ? (
                            <div className="p-8 text-center text-gray-500 dark:text-gray-400">Loading...</div>
                        ) : leaves && leaves.length > 0 ? (
                            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                                {leaves.map((leave: any) => (
                                    <li key={leave.id} className="p-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-3">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[leave.status]}`}>
                                                        {leave.status.toUpperCase()}
                                                    </span>
                                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                        {LEAVE_TYPES.find(t => t.value === leave.leave_type)?.label || leave.leave_type}
                                                    </span>
                                                </div>
                                                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                                    {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                                                    <span className="ml-2 text-gray-500">({leave.days_count} days)</span>
                                                </p>
                                                {leave.reason && (
                                                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-500 italic">"{leave.reason}"</p>
                                                )}
                                                {leave.admin_remarks && (
                                                    <p className="mt-1 text-sm text-indigo-600 dark:text-indigo-400">Admin: {leave.admin_remarks}</p>
                                                )}
                                            </div>
                                            {(leave.status === 'pending' || leave.status === 'approved') && new Date(leave.start_date) > new Date() && (
                                                <button
                                                    onClick={() => cancelMutation.mutate(leave.id)}
                                                    disabled={cancelMutation.isPending}
                                                    className="px-3 py-1 text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                                >
                                                    Cancel
                                                </button>
                                            )}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                                No leave requests yet. Click "Request Leave" to create one.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
