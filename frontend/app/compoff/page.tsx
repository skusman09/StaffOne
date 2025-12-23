'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { compoffAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { Clock, Plus, ClipboardList, Loader2 } from 'lucide-react'

export default function CompOffPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)
    const [showModal, setShowModal] = useState(false)
    const [formData, setFormData] = useState({
        ot_start_date: '',
        ot_end_date: '',
        reason: ''
    })

    useEffect(() => {
        setMounted(true)
    }, [])

    const { data: user } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: mounted && isAuthenticated(),
    })

    const { data: balance } = useQuery({
        queryKey: ['compoff-balance'],
        queryFn: compoffAPI.getBalance,
        enabled: mounted && isAuthenticated(),
    })

    const { data: requests, isLoading } = useQuery({
        queryKey: ['my-compoff-requests'],
        queryFn: () => compoffAPI.getMyRequests(),
        enabled: mounted && isAuthenticated(),
    })

    useEffect(() => {
        if (!mounted) return
        if (!isAuthenticated()) {
            router.push('/login')
        }
    }, [router, mounted])

    const requestMutation = useMutation({
        mutationFn: (data: any) => compoffAPI.request(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['my-compoff-requests'] })
            queryClient.invalidateQueries({ queryKey: ['compoff-balance'] })
            setShowModal(false)
            setFormData({ ot_start_date: '', ot_end_date: '', reason: '' })
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        requestMutation.mutate(formData)
    }

    if (!mounted) return null

    const statusColors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        approved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
        rejected: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
        used: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 sm:px-0">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-3">
                            <Clock className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Comp-off Requests</h1>
                                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Convert your overtime hours to compensatory leave</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setShowModal(true)}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center gap-1"
                        >
                            <Plus className="w-4 h-4" />
                            Request Comp-off
                        </button>
                    </div>

                    {/* Balance Card */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-indigo-500 p-6 rounded-xl shadow-lg">
                            <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Approved Days</p>
                            <p className="text-4xl font-mono font-bold text-white">{balance?.approved_days?.toFixed(1) || '0.0'}</p>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-emerald-500 p-6 rounded-xl shadow-lg">
                            <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Available Days</p>
                            <p className="text-4xl font-mono font-bold text-white">{balance?.available_days?.toFixed(1) || '0.0'}</p>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 border-l-4 border-l-blue-500 p-6 rounded-xl shadow-lg">
                            <p className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-1">Used Days</p>
                            <p className="text-4xl font-mono font-bold text-white">{balance?.used_days?.toFixed(1) || '0.0'}</p>
                        </div>
                    </div>

                    {/* Requests Table */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                            <ClipboardList className="w-5 h-5 text-indigo-500" />
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">My Requests</h2>
                        </div>
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-700/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OT Period</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OT Hours</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Days Earned</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {isLoading ? (
                                    <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">Loading...</td></tr>
                                ) : requests?.comp_offs?.length === 0 ? (
                                    <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No requests yet</td></tr>
                                ) : (
                                    requests?.comp_offs?.map((req: any) => (
                                        <tr key={req.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                            <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                                                {new Date(req.ot_start_date).toLocaleDateString()} - {new Date(req.ot_end_date).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{req.ot_hours.toFixed(1)} hrs</td>
                                            <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{req.comp_off_days.toFixed(2)}</td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[req.status]}`}>
                                                    {req.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </Container>

            {/* Request Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Request Comp-off Conversion</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">OT Start Date</label>
                                <input
                                    required
                                    type="date"
                                    value={formData.ot_start_date}
                                    onChange={(e) => setFormData({ ...formData, ot_start_date: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">OT End Date</label>
                                <input
                                    required
                                    type="date"
                                    value={formData.ot_end_date}
                                    onChange={(e) => setFormData({ ...formData, ot_end_date: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Reason (Optional)</label>
                                <textarea
                                    value={formData.reason}
                                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white h-24"
                                />
                            </div>
                            {requestMutation.isError && (
                                <p className="text-red-500 text-sm">{(requestMutation.error as any)?.response?.data?.detail || 'An error occurred'}</p>
                            )}
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={requestMutation.isPending}
                                    className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                                >
                                    {requestMutation.isPending ? 'Submitting...' : 'Submit Request'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
