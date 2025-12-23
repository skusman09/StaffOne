'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { configAPI, authAPI } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'

interface SystemConfig {
    key: string
    value: string
    description: string | null
    value_type: string
    created_at: string
    updated_at: string
}

// Group configs by category for better organization
const CONFIG_CATEGORIES: Record<string, { title: string; icon: string; keys: string[] }> = {
    working_hours: {
        title: 'Working Hours',
        icon: '⏰',
        keys: ['STANDARD_WORKING_HOURS', 'OFFICE_START_TIME', 'OFFICE_END_TIME', 'FULL_DAY_THRESHOLD_HOURS', 'HALF_DAY_THRESHOLD_HOURS']
    },
    overtime: {
        title: 'Overtime & Deductions',
        icon: '💰',
        keys: ['OVERTIME_MULTIPLIER', 'MAX_OVERTIME_HOURS_PER_DAY', 'DEDUCTION_RATE', 'EARLY_EXIT_PENALTY_RATE']
    },
    attendance: {
        title: 'Attendance Rules',
        icon: '📋',
        keys: ['LATE_ARRIVAL_GRACE_MINUTES', 'AUTO_CHECKOUT_HOURS', 'WEEKEND_DAYS']
    },
}

export default function SettingsPage() {
    const router = useRouter()
    const queryClient = useQueryClient()
    const [mounted, setMounted] = useState(false)
    const [editingConfig, setEditingConfig] = useState<SystemConfig | null>(null)
    const [editValue, setEditValue] = useState('')

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

    const { data: configData, isLoading, error } = useQuery({
        queryKey: ['system-configs'],
        queryFn: configAPI.getAll,
        enabled: mounted && isAuthenticated() && user?.role === 'admin',
    })

    const seedMutation = useMutation({
        mutationFn: configAPI.seed,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['system-configs'] })
        },
    })

    const updateMutation = useMutation({
        mutationFn: ({ key, value }: { key: string; value: string }) =>
            configAPI.update(key, { value }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['system-configs'] })
            setEditingConfig(null)
            setEditValue('')
        },
    })

    const openEditModal = (config: SystemConfig) => {
        setEditingConfig(config)
        setEditValue(config.value)
    }

    const closeEditModal = () => {
        setEditingConfig(null)
        setEditValue('')
    }

    const handleSave = () => {
        if (editingConfig) {
            updateMutation.mutate({ key: editingConfig.key, value: editValue })
        }
    }

    // Build configs map for easy lookup
    const configsMap: Record<string, SystemConfig> = {}
    if (configData?.configs) {
        for (const cfg of configData.configs) {
            configsMap[cfg.key] = cfg
        }
    }

    // Get uncategorized configs
    const categorizedKeys = new Set(Object.values(CONFIG_CATEGORIES).flatMap(c => c.keys))
    const uncategorizedConfigs = configData?.configs?.filter((c: SystemConfig) => !categorizedKeys.has(c.key)) || []

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

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Navbar />
            <Container className="py-6">
                <div className="px-4 py-6 sm:px-0">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">⚙️ System Settings</h1>
                            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                Configure business rules for attendance and salary calculations
                            </p>
                        </div>
                        <button
                            onClick={() => seedMutation.mutate()}
                            disabled={seedMutation.isPending}
                            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg font-medium transition-colors text-sm"
                        >
                            {seedMutation.isPending ? 'Seeding...' : '🌱 Seed Defaults'}
                        </button>
                    </div>

                    {isLoading ? (
                        <div className="text-center py-12 text-gray-500">Loading configurations...</div>
                    ) : error ? (
                        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
                            <p className="text-red-600 dark:text-red-400 mb-4">Failed to load configurations</p>
                            <button
                                onClick={() => seedMutation.mutate()}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm"
                            >
                                Seed Default Configurations
                            </button>
                        </div>
                    ) : configData?.configs?.length === 0 ? (
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center">
                            <p className="text-yellow-700 dark:text-yellow-400 mb-4">No configurations found. Click the button below to seed default settings.</p>
                            <button
                                onClick={() => seedMutation.mutate()}
                                disabled={seedMutation.isPending}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm"
                            >
                                {seedMutation.isPending ? 'Seeding...' : 'Seed Default Configurations'}
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Categorized Configs */}
                            {Object.entries(CONFIG_CATEGORIES).map(([catKey, category]) => {
                                const categoryConfigs = category.keys
                                    .map(key => configsMap[key])
                                    .filter(Boolean)

                                if (categoryConfigs.length === 0) return null

                                return (
                                    <div key={catKey} className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                                            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                                {category.icon} {category.title}
                                            </h2>
                                        </div>
                                        <div className="divide-y divide-gray-200 dark:divide-gray-700">
                                            {categoryConfigs.map((config) => (
                                                <div key={config.key} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-mono text-sm text-gray-900 dark:text-gray-100">{config.key}</span>
                                                            <span className="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                                                                {config.value_type}
                                                            </span>
                                                        </div>
                                                        {config.description && (
                                                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{config.description}</p>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-4">
                                                        <span className="font-semibold text-indigo-600 dark:text-indigo-400">{config.value}</span>
                                                        <button
                                                            onClick={() => openEditModal(config)}
                                                            className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-gray-700 dark:text-gray-300"
                                                        >
                                                            Edit
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )
                            })}

                            {/* Uncategorized Configs */}
                            {uncategorizedConfigs.length > 0 && (
                                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
                                    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                                        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                            📦 Other Settings
                                        </h2>
                                    </div>
                                    <div className="divide-y divide-gray-200 dark:divide-gray-700">
                                        {uncategorizedConfigs.map((config: SystemConfig) => (
                                            <div key={config.key} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-mono text-sm text-gray-900 dark:text-gray-100">{config.key}</span>
                                                        <span className="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                                                            {config.value_type}
                                                        </span>
                                                    </div>
                                                    {config.description && (
                                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{config.description}</p>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-4">
                                                    <span className="font-semibold text-indigo-600 dark:text-indigo-400">{config.value}</span>
                                                    <button
                                                        onClick={() => openEditModal(config)}
                                                        className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-gray-700 dark:text-gray-300"
                                                    >
                                                        Edit
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </Container>

            {/* Edit Modal */}
            {editingConfig && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                            Edit Configuration
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Key</label>
                                <input
                                    type="text"
                                    value={editingConfig.key}
                                    disabled
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-mono text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Value <span className="text-gray-400">({editingConfig.value_type})</span>
                                </label>
                                <input
                                    type={editingConfig.value_type === 'int' || editingConfig.value_type === 'float' ? 'number' : 'text'}
                                    step={editingConfig.value_type === 'float' ? '0.1' : undefined}
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                />
                            </div>
                            {editingConfig.description && (
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    💡 {editingConfig.description}
                                </p>
                            )}
                            {updateMutation.isError && (
                                <p className="text-sm text-red-600 dark:text-red-400">
                                    Failed to update configuration
                                </p>
                            )}
                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={closeEditModal}
                                    className="px-4 py-2 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={updateMutation.isPending}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg"
                                >
                                    {updateMutation.isPending ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
