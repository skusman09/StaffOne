'use client'

import { useEffect, useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leaveAPI, authAPI, adminAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import { toast } from '@/lib/toast'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { TableSkeleton } from '@/components/LoadingSkeleton'
import { getFullAvatarUrl } from '@/lib/utils'
import { CheckCircle2, XCircle, SearchX, Palmtree, Stethoscope, Calendar, CircleDollarSign, Baby, Heart, Files, Plane } from 'lucide-react'

const LEAVE_TYPE_ICONS: Record<string, any> = {
    annual: Palmtree,
    sick: Stethoscope,
    casual: Calendar,
    unpaid: CircleDollarSign,
    maternity: Baby,
    paternity: Baby,
    bereavement: Heart,
    other: Files,
}

const LEAVE_TYPES: Record<string, string> = {
    annual: 'Annual Leave',
    sick: 'Sick Leave',
    casual: 'Casual Leave',
    unpaid: 'Unpaid Leave',
    maternity: 'Maternity Leave',
    paternity: 'Paternity Leave',
    bereavement: 'Bereavement Leave',
    other: 'Other',
}

const STATUS_COLORS: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

export default function AdminLeavesPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [searchTerm, setSearchTerm] = useState('')

    // Approval/Rejection Modal State
    const [actionModal, setActionModal] = useState<{
        isOpen: boolean;
        type: 'approve' | 'reject';
        leaveId: number | null;
        employeeName: string;
        remarks: string;
    }>({
        isOpen: false,
        type: 'approve',
        leaveId: null,
        employeeName: '',
        remarks: '',
    })

    useEffect(() => {
        setMounted(true)
    }, [])

    const authed = mounted && isAuthenticated()

    // Redirect unauth/non-admin users
    const { data: user, isLoading: userLoading } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: authed,
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
    }, [mounted, user, router])

    const { data: leaves, isLoading: leavesLoading } = useQuery({
        queryKey: ['adminAllLeaves', statusFilter],
        queryFn: () => leaveAPI.getAll(0, 500, statusFilter === 'all' ? undefined : statusFilter),
        enabled: authed && user?.role === 'admin',
    })

    const approveMutation = useMutation({
        mutationFn: ({ id, remarks }: { id: number; remarks: string }) =>
            leaveAPI.approve(id, { admin_remarks: remarks }),
        onSuccess: () => {
            toast.success('Leave approved successfully')
            queryClient.invalidateQueries({ queryKey: ['adminAllLeaves'] })
            closeModal()
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.detail || 'Failed to approve leave')
        }
    })

    const rejectMutation = useMutation({
        mutationFn: ({ id, remarks }: { id: number; remarks: string }) =>
            leaveAPI.reject(id, { admin_remarks: remarks }),
        onSuccess: () => {
            toast.success('Leave rejected successfully')
            queryClient.invalidateQueries({ queryKey: ['adminAllLeaves'] })
            closeModal()
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.detail || 'Failed to reject leave')
        }
    })

    const filteredLeaves = useMemo(() => {
        if (!leaves) return []
        return leaves.filter((leave: any) => {
            const userName = (leave.user?.full_name || leave.user?.username || '').toLowerCase()
            const userEmail = (leave.user?.email || '').toLowerCase()
            const q = searchTerm.toLowerCase()
            return userName.includes(q) || userEmail.includes(q)
        })
    }, [leaves, searchTerm])

    const openModal = (type: 'approve' | 'reject', leave: any) => {
        setActionModal({
            isOpen: true,
            type,
            leaveId: leave.id,
            employeeName: leave.user?.full_name || leave.user?.username,
            remarks: '',
        })
    }

    const closeModal = () => {
        setActionModal(prev => ({ ...prev, isOpen: false }))
    }

    const handleAction = (e: React.FormEvent) => {
        e.preventDefault()
        if (!actionModal.leaveId) return

        if (actionModal.type === 'approve') {
            approveMutation.mutate({ id: actionModal.leaveId, remarks: actionModal.remarks })
        } else {
            rejectMutation.mutate({ id: actionModal.leaveId, remarks: actionModal.remarks })
        }
    }

    if (!mounted || userLoading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
                <Navbar />
                <Container className="py-6">
                    <TableSkeleton rows={5} />
                </Container>
            </div>
        )
    }

    if (user?.role !== 'admin') return null

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <Plane className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Leave Management</h1>
                        </div>
                        <p className="text-gray-500 dark:text-gray-400 mt-1">Review and manage employee leave requests</p>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                        <input
                            type="text"
                            placeholder="Search employee..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                        />
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                        >
                            <option value="all">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
                    {leavesLoading ? (
                        <div className="p-8"><TableSkeleton rows={5} /></div>
                    ) : filteredLeaves.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-900/50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Employee</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Dates</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Days</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                    {filteredLeaves.map((leave: any) => (
                                        <tr key={leave.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center text-indigo-700 dark:text-indigo-300 font-bold text-xs overflow-hidden">
                                                        {leave.user?.avatar_url ? (
                                                            <img
                                                                src={getFullAvatarUrl(leave.user.avatar_url) || undefined}
                                                                alt={leave.user?.username || 'User'}
                                                                className="w-full h-full object-cover"
                                                            />
                                                        ) : (
                                                            (leave.user?.full_name || leave.user?.username || 'U').charAt(0).toUpperCase()
                                                        )}
                                                    </div>
                                                    <div className="ml-4">
                                                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                            {leave.user?.username}
                                                        </div>
                                                        <div className="text-xs text-gray-500 dark:text-gray-400">{leave.user?.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    {(() => {
                                                        const Icon = LEAVE_TYPE_ICONS[leave.leave_type] || Files
                                                        return <Icon className="w-4 h-4 text-gray-400" />
                                                    })()}
                                                    <span className="text-sm text-gray-900 dark:text-gray-100">
                                                        {LEAVE_TYPES[leave.leave_type] || leave.leave_type}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="text-sm text-gray-900 dark:text-gray-100">
                                                    {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                {leave.days_count}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[leave.status]}`}>
                                                    {leave.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                {leave.status === 'pending' ? (
                                                    <div className="flex justify-end gap-2">
                                                        <button
                                                            onClick={() => openModal('approve', leave)}
                                                            className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                                                        >
                                                            Approve
                                                        </button>
                                                        <button
                                                            onClick={() => openModal('reject', leave)}
                                                            className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                                        >
                                                            Reject
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <span className="text-gray-400 italic">No actions</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="p-12 text-center text-gray-500 dark:text-gray-400 border border-dashed border-gray-300 dark:border-gray-700 rounded-lg m-4">
                            <SearchX className="mx-auto h-12 w-12 text-gray-400 mb-2" />
                            <p>No leave requests found matching your filters.</p>
                        </div>
                    )}
                </div>
            </Container>

            {/* Action Modal */}
            {actionModal.isOpen && (
                <div className="fixed inset-0 z-50 overflow-y-auto">
                    <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                        <div className="fixed inset-0 transition-opacity" aria-hidden="true" onClick={closeModal}>
                            <div className="absolute inset-0 bg-gray-500 dark:bg-gray-900 opacity-75"></div>
                        </div>

                        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                            <form onSubmit={handleAction}>
                                <div className="px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                    <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-gray-100 mb-4">
                                        {actionModal.type === 'approve' ? 'Approve' : 'Reject'} Leave Request
                                    </h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                                        Are you sure you want to {actionModal.type} the leave request for <strong>{actionModal.employeeName}</strong>?
                                    </p>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                            Admin Remarks (Optional)
                                        </label>
                                        <textarea
                                            value={actionModal.remarks}
                                            onChange={(e) => setActionModal({ ...actionModal, remarks: e.target.value })}
                                            rows={3}
                                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-indigo-500 focus:border-indigo-500"
                                            placeholder="Add a reason or comments..."
                                        />
                                    </div>
                                </div>
                                <div className="px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-3 bg-gray-50 dark:bg-gray-700/50">
                                    <button
                                        type="submit"
                                        disabled={approveMutation.isPending || rejectMutation.isPending}
                                        className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white sm:ml-3 sm:w-auto sm:text-sm ${actionModal.type === 'approve'
                                            ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
                                            : 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                                            }`}
                                    >
                                        {actionModal.type === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={closeModal}
                                        className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
