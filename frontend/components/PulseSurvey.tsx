'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pulseAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import { Send, CheckCircle2 } from 'lucide-react'

const ratings = [
    { value: 1, emoji: '😫', label: 'Stressed' },
    { value: 2, emoji: '😕', label: 'Down' },
    { value: 3, emoji: '😐', label: 'Okay' },
    { value: 4, emoji: '🙂', label: 'Good' },
    { value: 5, emoji: '🤩', label: 'Great' },
]

export default function PulseSurvey() {
    const queryClient = useQueryClient()
    const [selectedRating, setSelectedRating] = useState<number | null>(null)
    const [comment, setComment] = useState('')
    const [isSubmitted, setIsSubmitted] = useState(false)
    const [hasAlreadyResponded, setHasAlreadyResponded] = useState(false)

    const { data: activeSurvey, isLoading } = useQuery({
        queryKey: ['activePulseSurvey'],
        queryFn: pulseAPI.getActive,
        retry: false,
    })

    const mutation = useMutation({
        mutationFn: pulseAPI.respond,
        onSuccess: () => {
            setIsSubmitted(true)
            toast.success('Thank you for your feedback!')
            queryClient.invalidateQueries({ queryKey: ['activePulseSurvey'] })
        },
        onError: (error: any) => {
            const message = error.response?.data?.detail || 'Failed to submit response'
            if (message.includes('already responded')) {
                setHasAlreadyResponded(true)
            } else {
                toast.error(message)
            }
        },
    })

    if (isLoading || !activeSurvey) return null

    if (hasAlreadyResponded) {
        return (
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300">
                <div className="flex flex-col items-center justify-center space-y-3 py-4">
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400">
                        <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Already Responded</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
                        You've already shared your feedback for this survey. Thank you!
                    </p>
                </div>
            </div>
        )
    }

    if (isSubmitted) {
        return (
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300">
                <div className="flex flex-col items-center justify-center space-y-3 py-4">
                    <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-600 dark:text-green-400">
                        <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Feedback Received!</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
                        Your voice helps us make StaffOne better every day.
                    </p>
                </div>
            </div>
        )
    }

    const handleSubmit = () => {
        if (selectedRating === null) return
        mutation.mutate({
            survey_id: activeSurvey.id,
            rating: selectedRating,
            comment: comment || undefined,
        })
    }

    return (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="flex flex-col space-y-6">
                <div>
                    <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest bg-indigo-50 dark:bg-indigo-900/30 px-2 py-1 rounded-md mb-3 inline-block">
                        Quick Pulse
                    </span>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
                        {activeSurvey.question}
                    </h3>
                </div>

                <div className="flex justify-between items-center bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl">
                    {ratings.map((rating) => (
                        <button
                            key={rating.value}
                            onClick={() => setSelectedRating(rating.value)}
                            className={`flex flex-col items-center space-y-2 group transition-all duration-200 ${selectedRating === rating.value ? 'scale-110' : 'hover:scale-105 opacity-70 hover:opacity-100'
                                }`}
                        >
                            <span className={`text-3xl transition-transform ${selectedRating === rating.value ? 'grayscale-0' : 'grayscale'}`}>
                                {rating.emoji}
                            </span>
                            <span className={`text-[10px] font-medium transition-colors ${selectedRating === rating.value ? 'text-indigo-600 dark:text-indigo-400 font-bold' : 'text-slate-500'
                                }`}>
                                {rating.label}
                            </span>
                        </button>
                    ))}
                </div>

                {selectedRating !== null && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                        <textarea
                            placeholder="Any comments? (Optional)"
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            className="w-full h-20 p-3 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all resize-none"
                        />
                        <button
                            onClick={handleSubmit}
                            disabled={mutation.isPending}
                            className="w-full flex items-center justify-center space-x-2 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20"
                        >
                            {mutation.isPending ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Send className="w-4 h-4" />
                                    <span>Submit Feedback</span>
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
