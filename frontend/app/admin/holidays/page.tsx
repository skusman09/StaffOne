'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { holidayAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { CalendarClock, Plus, Loader2, CheckCircle2, Circle } from 'lucide-react'

interface Holiday {
    id: number
    holiday_date: string
    name: string
    description: string | null
    is_active: boolean
}

export default function HolidaysPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)

    const currentYear = new Date().getFullYear()
    const [selectedYear, setSelectedYear] = useState(currentYear)
    const [showModal, setShowModal] = useState(false)
    const [editingHoliday, setEditingHoliday] = useState<Holiday | null>(null)

    // Form state
    const [formDate, setFormDate] = useState('')
    const [formName, setFormName] = useState('')
    const [formDescription, setFormDescription] = useState('')

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

    const { data: holidaysData, isLoading } = useQuery({
        queryKey: ['holidays', selectedYear],
        queryFn: () => holidayAPI.getAll(selectedYear, false),
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
    })

    const createMutation = useMutation({
        mutationFn: (data: { holiday_date: string; name: string; description?: string }) => holidayAPI.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['holidays'] })
            closeModal()
        },
    })

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: any }) => holidayAPI.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['holidays'] })
            closeModal()
        },
    })

    const deleteMutation = useMutation({
        mutationFn: (id: number) => holidayAPI.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['holidays'] })
        },
    })

    const openCreateModal = () => {
        setEditingHoliday(null)
        setFormDate('')
        setFormName('')
        setFormDescription('')
        setShowModal(true)
    }

    const openEditModal = (holiday: Holiday) => {
        setEditingHoliday(holiday)
        setFormDate(holiday.holiday_date)
        setFormName(holiday.name)
        setFormDescription(holiday.description || '')
        setShowModal(true)
    }

    const closeModal = () => {
        setShowModal(false)
        setEditingHoliday(null)
        setFormDate('')
        setFormName('')
        setFormDescription('')
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const data = {
            holiday_date: formDate,
            name: formName,
            description: formDescription || undefined,
        }

        if (editingHoliday) {
            updateMutation.mutate({ id: editingHoliday.id, data })
        } else {
            createMutation.mutate(data)
        }
    }

    const handleDelete = (id: number) => {
        if (confirm('Are you sure you want to delete this holiday?')) {
            deleteMutation.mutate(id)
        }
    }

    const toggleActive = (holiday: Holiday) => {
        updateMutation.mutate({ id: holiday.id, data: { is_active: !holiday.is_active } })
    }

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

    const holidays = holidaysData?.holidays || []
    const yearOptions = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i)

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 py-6 sm:px-0">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <div className="flex items-center gap-3">
                                <CalendarClock className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Holiday Management</h1>
                            </div>
                            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                Manage company holidays (excluded from working days calculation)
                            </p>
                        </div>
                        <button
                            onClick={openCreateModal}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center gap-1"
                        >
                            <Plus className="w-4 h-4" />
                            Add Holiday
                        </button>
                    </div>

                    {/* Year Filter */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 mb-6">
                        <div className="flex items-center gap-4">
                            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Year:</label>
                            <select
                                value={selectedYear}
                                onChange={(e) => setSelectedYear(Number(e.target.value))}
                                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            >
                                {yearOptions.map((year) => (
                                    <option key={year} value={year}>{year}</option>
                                ))}
                            </select>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                                {holidays.length} holiday{holidays.length !== 1 ? 's' : ''} found
                            </span>
                        </div>
                    </div>

                    {/* Holidays Table */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                        {isLoading ? (
                            <div className="p-12 text-center text-gray-500">
                                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-indigo-600" />
                                <p>Loading holidays...</p>
                            </div>
                        ) : holidays.length === 0 ? (
                            <div className="p-12 text-center">
                                <p className="text-gray-500 dark:text-gray-400 mb-4">No holidays found for {selectedYear}.</p>
                                <button
                                    onClick={openCreateModal}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm"
                                >
                                    Add First Holiday
                                </button>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                    <thead className="bg-gray-50 dark:bg-gray-900">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Description</th>
                                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                        {holidays.map((holiday: Holiday) => (
                                            <tr key={holiday.id} className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${!holiday.is_active ? 'opacity-50' : ''}`}>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                        {new Date(holiday.holiday_date).toLocaleDateString('en-US', {
                                                            weekday: 'short',
                                                            year: 'numeric',
                                                            month: 'short',
                                                            day: 'numeric'
                                                        })}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{holiday.name}</div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm text-gray-500 dark:text-gray-400">{holiday.description || '-'}</div>
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <button
                                                        onClick={() => toggleActive(holiday)}
                                                        className={`px-2 py-1 text-xs rounded-full flex items-center gap-1 ${holiday.is_active
                                                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                                                            }`}
                                                    >
                                                        {holiday.is_active ? (
                                                            <>
                                                                <CheckCircle2 className="w-3 h-3" />
                                                                Active
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Circle className="w-3 h-3" />
                                                                Inactive
                                                            </>
                                                        )}
                                                    </button>
                                                </td>
                                                <td className="px-6 py-4 text-right space-x-2">
                                                    <button
                                                        onClick={() => openEditModal(holiday)}
                                                        className="text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 text-sm"
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(holiday.id)}
                                                        className="text-red-600 hover:text-red-800 dark:text-red-400 text-sm"
                                                    >
                                                        Delete
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </Container>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                            {editingHoliday ? 'Edit Holiday' : 'Add Holiday'}
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date</label>
                                <input
                                    type="date"
                                    value={formDate}
                                    onChange={(e) => setFormDate(e.target.value)}
                                    required
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={formName}
                                    onChange={(e) => setFormName(e.target.value)}
                                    required
                                    placeholder="e.g., Diwali, Christmas"
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description (Optional)</label>
                                <textarea
                                    value={formDescription}
                                    onChange={(e) => setFormDescription(e.target.value)}
                                    rows={2}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    className="px-4 py-2 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={createMutation.isPending || updateMutation.isPending}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg"
                                >
                                    {editingHoliday ? 'Update' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
