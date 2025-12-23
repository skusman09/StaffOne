'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { compoffAPI, adminAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'

export default function AdminCompOffPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)
    const [selectedRequest, setSelectedRequest] = useState<any | null>(null)
    const [reviewData, setReviewData] = useState({ status: 'approved', admin_remarks: '' })

    useEffect(() => {
        setMounted(true)
    }, [])

    const { data: user } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: mounted && isAuthenticated(),
    })

    const { data: requests, isLoading } = useQuery({
        queryKey: ['admin-compoff-requests'],
        queryFn: () => compoffAPI.getAll(),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
    })

    const { data: usersData } = useQuery({
        queryKey: ['all-users-short'],
        queryFn: () => adminAPI.getUsers(0, 500),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
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

    const reviewMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: any }) => compoffAPI.review(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-compoff-requests'] })
            setSelectedRequest(null)
        },
    })

    const handleReview = (e: React.FormEvent) => {
        e.preventDefault()
        if (selectedRequest) {
            reviewMutation.mutate({ id: selectedRequest.id, data: reviewData })
        }
    }

    if (!mounted || !user || user.role !== 'admin') return null

    const statusColors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        used: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    }

    const getUserName = (userId: number) => {
        const u = usersData?.find((u: any) => u.id === userId)
        return u?.full_name || u?.username || `User #${userId}`
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />

            <Container className="py-6">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">🏖️ Manage Comp-off Requests</h1>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Review and approve employee comp-off conversion requests</p>
                </div>

                {/* Requests Table */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700/50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Employee</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OT Period</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OT Hours</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Days</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {isLoading ? (
                                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">Loading...</td></tr>
                            ) : requests?.comp_offs?.length === 0 ? (
                                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No requests found</td></tr>
                            ) : (
                                requests?.comp_offs?.map((req: any) => (
                                    <tr key={req.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                        <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{getUserName(req.user_id)}</td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                                            {new Date(req.ot_start_date).toLocaleDateString()} - {new Date(req.ot_end_date).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{req.ot_hours.toFixed(1)} hrs</td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{req.comp_off_days.toFixed(2)}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[req.status]}`}>
                                                {req.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {req.status === 'pending' && (
                                                <button
                                                    onClick={() => { setSelectedRequest(req); setReviewData({ status: 'approved', admin_remarks: '' }); }}
                                                    className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium"
                                                >
                                                    Review
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </Container>

            {/* Review Modal */}
            {
                selectedRequest && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Review Comp-off Request</h2>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                                <strong>{getUserName(selectedRequest.user_id)}</strong> is requesting conversion of <strong>{selectedRequest.ot_hours.toFixed(1)} OT hours</strong> to <strong>{selectedRequest.comp_off_days.toFixed(2)} days</strong>.
                            </p>
                            <form onSubmit={handleReview} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Decision</label>
                                    <select
                                        value={reviewData.status}
                                        onChange={(e) => setReviewData({ ...reviewData, status: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                    >
                                        <option value="approved">Approve</option>
                                        <option value="rejected">Reject</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Remarks (Optional)</label>
                                    <textarea
                                        value={reviewData.admin_remarks}
                                        onChange={(e) => setReviewData({ ...reviewData, admin_remarks: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white h-24"
                                    />
                                </div>
                                <div className="flex gap-3 pt-2">
                                    <button
                                        type="button"
                                        onClick={() => setSelectedRequest(null)}
                                        className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={reviewMutation.isPending}
                                        className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                                    >
                                        {reviewMutation.isPending ? 'Submitting...' : 'Submit'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )
            }
        </div >
    )
}
