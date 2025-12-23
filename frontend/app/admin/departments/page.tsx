'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { departmentAPI, adminAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { Building2, Plus, Loader2 } from 'lucide-react'

export default function DepartmentsPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [editingDept, setEditingDept] = useState<any | null>(null)
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        manager_id: ''
    })

    useEffect(() => {
        setMounted(true)
    }, [])

    const { data: user } = useQuery({
        queryKey: ['user'],
        queryFn: authAPI.me,
        enabled: mounted && isAuthenticated(),
    })

    const { data: deptData, isLoading } = useQuery({
        queryKey: ['departments'],
        queryFn: departmentAPI.getAll,
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

    const createMutation = useMutation({
        mutationFn: (data: any) => departmentAPI.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['departments'] })
            setIsModalOpen(false)
            resetForm()
        },
    })

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: any }) => departmentAPI.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['departments'] })
            setIsModalOpen(false)
            resetForm()
        },
    })

    const deleteMutation = useMutation({
        mutationFn: (id: number) => departmentAPI.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['departments'] })
        },
    })

    const resetForm = () => {
        setFormData({ name: '', description: '', manager_id: '' })
        setEditingDept(null)
    }

    const handleEdit = (dept: any) => {
        setEditingDept(dept)
        setFormData({
            name: dept.name,
            description: dept.description || '',
            manager_id: dept.manager_id?.toString() || ''
        })
        setIsModalOpen(true)
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const payload = {
            ...formData,
            manager_id: formData.manager_id ? parseInt(formData.manager_id) : null
        }

        if (editingDept) {
            updateMutation.mutate({ id: editingDept.id, data: payload })
        } else {
            createMutation.mutate(payload)
        }
    }

    if (!mounted || !user || user.role !== 'admin') return null

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <div className="flex items-center gap-3">
                            <Building2 className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Department Management</h1>
                        </div>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Manage organizational divisions and managers</p>
                    </div>
                    <button
                        onClick={() => { resetForm(); setIsModalOpen(true); }}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center gap-1"
                    >
                        <Plus className="w-4 h-4" />
                        New Department
                    </button>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700/50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Description</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Manager</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {isLoading ? (
                                <tr>
                                    <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                                        <div className="flex flex-col items-center gap-2">
                                            <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
                                            <span>Loading...</span>
                                        </div>
                                    </td>
                                </tr>
                            ) : deptData?.departments?.length === 0 ? (
                                <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No departments found</td></tr>
                            ) : (
                                deptData?.departments?.map((dept: any) => (
                                    <tr key={dept.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{dept.name}</td>
                                        <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{dept.description || '-'}</td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                            {usersData?.users?.find((u: any) => u.id === dept.manager_id)?.full_name || '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button onClick={() => handleEdit(dept)} className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-4">Edit</button>
                                            <button
                                                onClick={() => { if (confirm('Are you sure?')) deleteMutation.mutate(dept.id) }}
                                                className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </Container>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md p-6">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                            {editingDept ? 'Edit Department' : 'Create Department'}
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                                <input
                                    required
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white h-24"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manager</label>
                                <select
                                    value={formData.manager_id}
                                    onChange={(e) => setFormData({ ...formData, manager_id: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                >
                                    <option value="">Select Manager</option>
                                    {usersData?.users?.map((u: any) => (
                                        <option key={u.id} value={u.id}>{u.full_name || u.username}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={createMutation.isPending || updateMutation.isPending}
                                    className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                                >
                                    {(createMutation.isPending || updateMutation.isPending) ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
