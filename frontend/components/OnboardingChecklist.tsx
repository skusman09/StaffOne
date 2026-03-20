'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { onboardingAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import {
    CheckCircle2,
    Circle,
    ChevronDown,
    ChevronUp,
    ClipboardCheck,
    Loader2,
    PartyPopper
} from 'lucide-react'

export default function OnboardingChecklist() {
    const queryClient = useQueryClient()
    const [expandedOb, setExpandedOb] = useState<number | null>(null)

    const { data: summaries, isLoading } = useQuery({
        queryKey: ['onboardingSummaries'],
        queryFn: onboardingAPI.getMyOnboardings,
    })

    const { data: detail, isFetching: isDetailFetching } = useQuery({
        queryKey: ['onboardingDetail', expandedOb],
        queryFn: () => expandedOb ? onboardingAPI.getOnboardingDetail(expandedOb) : null,
        enabled: !!expandedOb,
    })

    const mutation = useMutation({
        mutationFn: ({ progressId, is_completed }: { progressId: number; is_completed: boolean }) =>
            onboardingAPI.updateTaskProgress(progressId, { is_completed }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['onboardingSummaries'] })
            queryClient.invalidateQueries({ queryKey: ['onboardingDetail', expandedOb] })
            toast.success('Task status updated!')
        },
        onError: () => {
            toast.error('Failed to update task')
        }
    })

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
            </div>
        )
    }

    if (!summaries || summaries.length === 0) return null

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
                <ClipboardCheck className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">Your Onboarding</h2>
            </div>

            {summaries.map((summary: any) => (
                <div
                    key={summary.id}
                    className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm hover:shadow-md transition-all duration-300"
                >
                    {/* Summary Header */}
                    <div
                        className="p-5 cursor-pointer flex items-center justify-between"
                        onClick={() => setExpandedOb(expandedOb === summary.id ? null : summary.id)}
                    >
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                                <h3 className="font-bold text-slate-900 dark:text-white">{summary.workflow_title}</h3>
                                {summary.status === 'completed' && (
                                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full uppercase">
                                        <PartyPopper className="w-3 h-3" /> Completed
                                    </span>
                                )}
                            </div>

                            {/* Progress Bar */}
                            <div className="flex items-center gap-3">
                                <div className="flex-1 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-indigo-600 transition-all duration-500 ease-out"
                                        style={{ width: `${summary.progress_percentage}%` }}
                                    />
                                </div>
                                <span className="text-xs font-bold text-slate-500">
                                    {Math.round(summary.progress_percentage)}%
                                </span>
                            </div>
                            <p className="text-[10px] text-slate-400 mt-2">
                                {summary.tasks_completed} of {summary.tasks_total} tasks completed
                            </p>
                        </div>

                        <div className="ml-4 text-slate-400">
                            {expandedOb === summary.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                        </div>
                    </div>

                    {/* Details / Task List */}
                    {expandedOb === summary.id && (
                        <div className="border-t border-slate-100 dark:border-slate-800 p-5 bg-slate-50/50 dark:bg-slate-800/20">
                            {isDetailFetching && !detail ? (
                                <div className="flex justify-center py-4">
                                    <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {detail?.task_progress.sort((a: any, b: any) => a.task.order - b.task.order).map((prog: any) => (
                                        <div
                                            key={prog.id}
                                            className={`flex items-start gap-3 p-3 rounded-xl transition-all ${prog.is_completed
                                                    ? 'opacity-60 grayscale-[0.5]'
                                                    : 'bg-white dark:bg-slate-900 shadow-sm'
                                                }`}
                                        >
                                            <button
                                                onClick={() => mutation.mutate({ progressId: prog.id, is_completed: !prog.is_completed })}
                                                disabled={mutation.isPending}
                                                className={`mt-0.5 transition-colors ${prog.is_completed ? 'text-emerald-500' : 'text-slate-300 hover:text-indigo-500'
                                                    }`}
                                            >
                                                {prog.is_completed ? (
                                                    <CheckCircle2 className="w-5 h-5" />
                                                ) : (
                                                    <Circle className="w-5 h-5" />
                                                )}
                                            </button>
                                            <div>
                                                <h4 className={`text-sm font-bold ${prog.is_completed ? 'line-through text-slate-500' : 'text-slate-900 dark:text-white'}`}>
                                                    {prog.task.title}
                                                </h4>
                                                {prog.task.description && !prog.is_completed && (
                                                    <p className="text-xs text-slate-500 mt-1">{prog.task.description}</p>
                                                )}
                                                {prog.is_completed && prog.completed_at && (
                                                    <p className="text-[10px] text-emerald-500 mt-1 uppercase font-semibold">
                                                        Completed {new Date(prog.completed_at).toLocaleDateString()}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ))}
        </div>
    )
}
