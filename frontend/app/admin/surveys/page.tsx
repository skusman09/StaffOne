'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pulseAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import { 
  Plus, 
  Edit2, 
  Trash2, 
  BarChart3, 
  Eye, 
  EyeOff,
  Calendar,
  MessageSquare,
  TrendingUp
} from 'lucide-react'
import Link from 'next/link'
import Container from '@/components/Container'
import Navbar from '@/components/Navbar'

interface Survey {
  id: number
  question: string
  is_active: boolean
  created_at: string
  response_count?: number
  average_rating?: number
}

export default function SurveyManagement() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingSurvey, setEditingSurvey] = useState<Survey | null>(null)
  const [newQuestion, setNewQuestion] = useState('')

  const { data: surveys, isLoading } = useQuery({
    queryKey: ['adminSurveys'],
    queryFn: pulseAPI.admin.getAll,
  })

  const createMutation = useMutation({
    mutationFn: pulseAPI.admin.create,
    onSuccess: () => {
      toast.success('Survey created successfully!')
      setNewQuestion('')
      setShowCreateForm(false)
      queryClient.invalidateQueries({ queryKey: ['adminSurveys'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create survey')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => 
      pulseAPI.admin.update(id, data),
    onSuccess: () => {
      toast.success('Survey updated successfully!')
      setEditingSurvey(null)
      queryClient.invalidateQueries({ queryKey: ['adminSurveys'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update survey')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: pulseAPI.admin.delete,
    onSuccess: () => {
      toast.success('Survey deleted successfully!')
      queryClient.invalidateQueries({ queryKey: ['adminSurveys'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete survey')
    },
  })

  const handleCreate = () => {
    if (!newQuestion.trim()) return
    createMutation.mutate({ question: newQuestion.trim() })
  }

  const handleUpdate = (id: number, isActive: boolean) => {
    updateMutation.mutate({ id, data: { is_active: isActive } })
  }

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this survey?')) {
      deleteMutation.mutate(id)
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
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Survey Management
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Create and manage pulse surveys for employee feedback
              </p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Create Survey</span>
            </button>
          </div>

          {/* Create Survey Form */}
          {showCreateForm && (
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 mb-8">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Create New Survey
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Survey Question
                  </label>
                  <input
                    type="text"
                    value={newQuestion}
                    onChange={(e) => setNewQuestion(e.target.value)}
                    placeholder="How satisfied are you with..."
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={handleCreate}
                    disabled={createMutation.isPending || !newQuestion.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
                  >
                    {createMutation.isPending ? 'Creating...' : 'Create Survey'}
                  </button>
                  <button
                    onClick={() => {
                      setShowCreateForm(false)
                      setNewQuestion('')
                    }}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Surveys List */}
          <div className="space-y-4">
            {surveys?.map((survey: Survey) => (
              <div
                key={survey.id}
                className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                      {survey.question}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-slate-600 dark:text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(survey.created_at).toLocaleDateString()}</span>
                      </span>
                      {survey.response_count !== undefined && (
                        <span className="flex items-center space-x-1">
                          <MessageSquare className="w-4 h-4" />
                          <span>{survey.response_count} responses</span>
                        </span>
                      )}
                      {survey.average_rating !== undefined && (
                        <span className="flex items-center space-x-1">
                          <TrendingUp className="w-4 h-4" />
                          <span>Avg: {survey.average_rating.toFixed(1)}/5</span>
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleUpdate(survey.id, !survey.is_active)}
                      className={`p-2 rounded-lg transition-colors ${
                        survey.is_active
                          ? 'bg-green-100 text-green-600 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-400'
                      }`}
                      title={survey.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {survey.is_active ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => setEditingSurvey(survey)}
                      className="p-2 bg-blue-100 text-blue-600 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 rounded-lg transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(survey.id)}
                      className="p-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <Link 
                      href={`/admin/surveys/${survey.id}`}
                      className="p-2 bg-indigo-100 text-indigo-600 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 rounded-lg transition-colors"
                      title="View Analytics"
                    >
                      <BarChart3 className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
            
            {surveys?.length === 0 && (
              <div className="text-center py-12">
                <MessageSquare className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                  No surveys yet
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  Create your first pulse survey to start collecting feedback
                </p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                >
                  Create Survey
                </button>
              </div>
            )}
          </div>
        </div>
      </Container>
    </div>
  )
}
