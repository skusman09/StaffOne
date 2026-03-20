'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { onboardingAPI, notificationAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import Navbar from '@/components/Navbar'
import Container from '@/components/Container'
import { Clock, CheckCircle2, Users, FileText, Bell, Calendar, MessageSquare } from 'lucide-react'

interface OnboardingAssignment {
  id: number
  status: string
  started_at: string
  completed_at?: string
  user: {
    username: string
    email: string
  }
  workflow: {
    id: number
    title: string
    description?: string
  }
  progress_percentage: number
  tasks_total: number
  tasks_completed: number
}

interface Note {
  id: number
  note: string
  created_at: string
  admin: {
    username: string
    email: string
  }
}

export default function EmployeeOnboardingPage() {
  const queryClient = useQueryClient()
  const [selectedAssignment, setSelectedAssignment] = useState<OnboardingAssignment | null>(null)
  const [showNotes, setShowNotes] = useState(false)

  const { data: onboardings = [], isLoading } = useQuery({
    queryKey: ['employeeOnboardings'],
    queryFn: onboardingAPI.getMyOnboardings,
  })

  const { data: notes = [], isLoading: notesLoading } = useQuery({
    queryKey: ['assignmentNotes', selectedAssignment?.id],
    queryFn: () => onboardingAPI.admin.getNotes(selectedAssignment!.id),
    enabled: !!selectedAssignment && showNotes,
  })

  const updateTaskMutation = useMutation({
    mutationFn: ({ progressId, isCompleted }: { progressId: number; isCompleted: boolean }) =>
      onboardingAPI.updateTaskProgress(progressId, { is_completed: isCompleted }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employeeOnboardings'] })
      toast.success('Task updated successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update task')
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100 dark:bg-green-900/30'
      case 'in_progress': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30'
      default: return 'text-slate-600 bg-slate-100 dark:bg-slate-700/50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4" />
      case 'in_progress': return <Clock className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
        <Navbar />
        <Container>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        </Container>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Navbar />
      <Container>
        <div className="py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              My Onboarding
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Track your onboarding progress and view admin notes
            </p>
          </div>

          {onboardings.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                No Onboarding Assigned
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                You haven't been assigned any onboarding workflows yet.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {onboardings.map((assignment: OnboardingAssignment) => (
                <div key={assignment.id} className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        {assignment.workflow.title}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {assignment.workflow.description}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-1 ${getStatusColor(assignment.status)}`}>
                        {getStatusIcon(assignment.status)}
                        <span>{assignment.status.replace('_', ' ')}</span>
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                        {assignment.progress_percentage}%
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">Complete</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-slate-900 dark:text-white">
                        {assignment.tasks_completed}/{assignment.tasks_total}
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">Tasks Done</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-slate-900 dark:text-white">
                        {new Date(assignment.started_at).toLocaleDateString()}
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">Start Date</div>
                    </div>
                  </div>

                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 mb-6">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${assignment.progress_percentage}%` }}
                    />
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => {
                        setSelectedAssignment(assignment)
                        setShowNotes(true)
                      }}
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>View Notes</span>
                    </button>
                    <button
                      onClick={() => window.location.href = `/onboarding/${assignment.id}/tasks`}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                    >
                      View Tasks
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Notes Modal */}
        {selectedAssignment && showNotes && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen p-4">
              <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={() => setShowNotes(false)}></div>
              
              <div className="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
                <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
                  <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                    Notes for {selectedAssignment.workflow.title}
                  </h2>
                  <button
                    onClick={() => setShowNotes(false)}
                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    ×
                  </button>
                </div>
                
                <div className="p-6 overflow-y-auto max-h-[60vh]">
                  {notesLoading ? (
                    <div className="flex items-center justify-center h-32">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                    </div>
                  ) : notes.length > 0 ? (
                    <div className="space-y-4">
                      {notes.map((note: Note) => (
                        <div key={note.id} className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <div className="w-8 h-8 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center">
                                <Users className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                              </div>
                              <div>
                                <p className="font-medium text-slate-900 dark:text-white">
                                  {note.admin.username}
                                </p>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                  {note.admin.email}
                                </p>
                              </div>
                            </div>
                            <span className="text-xs text-slate-500 dark:text-slate-400">
                              {new Date(note.created_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-slate-700 dark:text-slate-300">
                            {note.note}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <MessageSquare className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
                      <p className="text-slate-600 dark:text-slate-400">
                        No notes added yet
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </Container>
    </div>
  )
}
