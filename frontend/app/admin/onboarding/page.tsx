'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { onboardingAPI, adminAPI } from '@/lib/api'
import { toast } from '@/lib/toast'
import {
  Plus,
  Edit2,
  Trash2,
  Users,
  CheckCircle2,
  Clock,
  FileText,
  UserPlus,
  BarChart3,
  Calendar,
  X
} from 'lucide-react'
import Container from '@/components/Container'
import Navbar from '@/components/Navbar'
import OnboardingModal from '@/components/OnboardingModal'

interface OnboardingTemplate {
  id: number
  title: string
  description: string
  is_active: boolean
  created_at: string
  tasks: Array<{
    id: number
    title: string
    description: string
    order: number
    is_required: boolean
  }>
}

interface EmployeeAssignment {
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
    tasks: Array<{
      id: number
      title: string
      description: string
      order: number
      is_required: boolean
    }>
  }
  progress_percentage: number
  tasks_total: number
  tasks_completed: number
  employee_tasks: Array<{
    id: number
    task_id: number
    status: 'pending' | 'in_progress' | 'completed'
    completed_at?: string
    task: {
      id: number
      title: string
      description: string
      order: number
      is_required: boolean
    }
  }>
}

export default function OnboardingManagement() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<OnboardingTemplate | null>(null)
  const [selectedAssignment, setSelectedAssignment] = useState<EmployeeAssignment | null>(null)
  const [activeTab, setActiveTab] = useState<'templates' | 'assignments'>('templates')
  const [deleteConfirmation, setDeleteConfirmation] = useState<{ id: number; title: string } | null>(null)
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [noteText, setNoteText] = useState('')

  // Template form state
  const [templateTitle, setTemplateTitle] = useState('')
  const [templateDescription, setTemplateDescription] = useState('')
  const [tasks, setTasks] = useState([
    { title: '', description: '', order: 1, is_required: true }
  ])

  // Assignment form state
  const [selectedWorkflow, setSelectedWorkflow] = useState('')
  const [selectedUser, setSelectedUser] = useState('')

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ['onboardingTemplates'],
    queryFn: onboardingAPI.admin.getTemplates,
  })

  const { data: assignments, isLoading: assignmentsLoading } = useQuery({
    queryKey: ['onboardingAssignments'],
    queryFn: onboardingAPI.admin.getAssignments,
  })

  const { data: employees, isLoading: employeesLoading } = useQuery({
    queryKey: ['employees'],
    queryFn: () => adminAPI.getUsers(0, 1000), // Get all users
  })

  const updateTemplateMutation = useMutation({
    mutationFn: (data: { id: number; templateData: any }) =>
      onboardingAPI.admin.updateTemplate(data.id, data.templateData),
    onSuccess: () => {
      toast.success('Template updated successfully!')
      resetTemplateForm()
      queryClient.invalidateQueries({ queryKey: ['onboardingTemplates'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update template')
    },
  })

  const createTemplateMutation = useMutation({
    mutationFn: onboardingAPI.admin.createTemplate,
    onSuccess: () => {
      toast.success('Template created successfully!')
      resetTemplateForm()
      queryClient.invalidateQueries({ queryKey: ['onboardingTemplates'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create template')
    },
  })

  const assignWorkflowMutation = useMutation({
    mutationFn: onboardingAPI.admin.assign,
    onSuccess: () => {
      toast.success('Onboarding assigned successfully!')
      resetAssignForm()
      queryClient.invalidateQueries({ queryKey: ['onboardingAssignments'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign onboarding')
    },
  })

  const handleEditTemplate = (template: OnboardingTemplate) => {
    setEditingTemplate(template)
    setTemplateTitle(template.title)
    setTemplateDescription(template.description)
    setTasks(template.tasks.map(task => ({
      title: task.title,
      description: task.description,
      order: task.order,
      is_required: task.is_required
    })))
    setShowCreateForm(true)
  }

  const resetTemplateForm = () => {
    setTemplateTitle('')
    setTemplateDescription('')
    setTasks([{ title: '', description: '', order: 1, is_required: true }])
    setEditingTemplate(null)
    setShowCreateForm(false)
  }

  const resetAssignForm = () => {
    setSelectedWorkflow('')
    setSelectedUser('')
    setShowAssignForm(false)
  }

  const addTask = () => {
    const newTask = { title: '', description: '', order: tasks.length + 1, is_required: true }
    setTasks([...tasks, newTask])
    // Focus on the new task's title input after a short delay
    setTimeout(() => {
      const taskInputs = document.querySelectorAll('input[placeholder="Task title"]')
      if (taskInputs.length > 0) {
        const lastInput = taskInputs[taskInputs.length - 1] as HTMLInputElement
        lastInput.focus()
      }
    }, 100)
  }

  const updateTask = (index: number, field: string, value: any) => {
    const updatedTasks = [...tasks]
    updatedTasks[index] = { ...updatedTasks[index], [field]: value }
    setTasks(updatedTasks)
  }

  const removeTask = (index: number) => {
    if (tasks.length > 1) {
      setTasks(tasks.filter((_, i) => i !== index))
    }
  }

  const handleCreateTemplate = () => {
    if (!templateTitle.trim() || tasks.some(task => !task.title.trim())) {
      toast.error('Please fill in template title and all task titles')
      return
    }

    const templateData = {
      title: templateTitle.trim(),
      description: templateDescription.trim(),
      is_active: true,
      tasks: tasks.map((task, index) => ({
        ...task,
        order: index + 1,
        title: task.title.trim(),
        description: task.description.trim()
      }))
    }

    if (editingTemplate) {
      updateTemplateMutation.mutate({
        id: editingTemplate.id,
        templateData
      })
    } else {
      createTemplateMutation.mutate(templateData)
    }
  }

  const deleteTemplateMutation = useMutation({
    mutationFn: onboardingAPI.admin.deleteTemplate,
    onSuccess: () => {
      toast.success('Template deleted successfully!')
      queryClient.invalidateQueries({ queryKey: ['onboardingTemplates'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete template')
    },
  })

  const handleDeleteTemplate = (templateId: number, templateTitle: string) => {
    setDeleteConfirmation({ id: templateId, title: templateTitle })
  }

  const confirmDelete = () => {
    if (deleteConfirmation) {
      deleteTemplateMutation.mutate(deleteConfirmation.id)
      setDeleteConfirmation(null)
    }
  }

  const handleSendReminder = async () => {
    if (selectedAssignment) {
      try {
        await onboardingAPI.admin.sendReminder(selectedAssignment.id)
        toast.success(`Reminder sent to ${selectedAssignment.user.username} for onboarding tasks`)
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to send reminder')
      }
    }
  }

  const handleAddNote = async () => {
    if (selectedAssignment && noteText.trim()) {
      try {
        await onboardingAPI.admin.addNote(selectedAssignment.id, noteText)
        toast.success(`Note added for ${selectedAssignment.user.username}`)
        setNoteText('')
        setShowNoteModal(false)
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to add note')
      }
    }
  }

  const handleAssign = () => {
    if (!selectedWorkflow || !selectedUser) {
      toast.error('Please select workflow and user')
      return
    }

    assignWorkflowMutation.mutate({
      user_id: parseInt(selectedUser),
      workflow_id: parseInt(selectedWorkflow)
    })
  }

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

  if (templatesLoading || assignmentsLoading) {
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
                Onboarding Management
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Create templates and manage employee onboarding
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowCreateForm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
              >
                <FileText className="w-4 h-4" />
                <span>Create Template</span>
              </button>
              <button
                onClick={() => setShowAssignForm(true)}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                <UserPlus className="w-4 h-4" />
                <span>Assign Onboarding</span>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 mb-8 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('templates')}
              className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${activeTab === 'templates'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
            >
              <FileText className="w-4 h-4" />
              <span>Templates</span>
            </button>
            <button
              onClick={() => setActiveTab('assignments')}
              className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${activeTab === 'assignments'
                ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
            >
              <Users className="w-4 h-4" />
              <span>Assignments</span>
            </button>
          </div>

          {/* Create/Edit Template Modal */}
          <OnboardingModal
            isOpen={showCreateForm}
            onClose={resetTemplateForm}
            title={editingTemplate ? 'Edit Template' : 'Create Template'}
          >
            <div className="space-y-3">
              {editingTemplate && (
                <div className="bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 px-3 py-2 rounded-lg text-sm border border-indigo-200 dark:border-indigo-800">
                  Editing: <strong>{editingTemplate.title}</strong>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={templateTitle}
                  onChange={(e) => setTemplateTitle(e.target.value)}
                  placeholder="e.g., Standard Employee Onboarding"
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  placeholder="Describe what this onboarding covers..."
                  rows={2}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm resize-none"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                    Tasks
                  </label>
                  <button
                    onClick={addTask}
                    className="px-2 py-1 bg-indigo-100 text-indigo-600 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 rounded text-xs transition-colors"
                  >
                    + Add Task
                  </button>
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto overflow-x-hidden custom-scrollbar">
                  {tasks.map((task, index) => (
                    <div key={index} className="flex items-start space-x-2 p-2 border border-slate-200 dark:border-slate-700 rounded-lg">
                      <div className="flex-shrink-0 w-5 text-center">
                        <span className="text-xs font-medium text-slate-500">
                          {index + 1}
                        </span>
                      </div>
                      <div className="flex-1 space-y-1">
                        <input
                          type="text"
                          value={task.title}
                          onChange={(e) => updateTask(index, 'title', e.target.value)}
                          placeholder="Task title"
                          className="w-full px-2 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-xs focus:ring-1 focus:ring-indigo-500 focus:border-transparent"
                        />
                        <input
                          type="text"
                          value={task.description}
                          onChange={(e) => updateTask(index, 'description', e.target.value)}
                          placeholder="Description (optional)"
                          className="w-full px-2 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-xs focus:ring-1 focus:ring-indigo-500 focus:border-transparent"
                        />
                      </div>
                      <div className="flex items-center space-x-1">
                        <label className="flex items-center space-x-1">
                          <input
                            type="checkbox"
                            checked={task.is_required}
                            onChange={(e) => updateTask(index, 'is_required', e.target.checked)}
                            className="rounded text-indigo-600 focus:ring-indigo-500 w-3 h-3"
                          />
                          <span className="text-xs text-slate-600 dark:text-slate-400">Req</span>
                        </label>
                        {tasks.length > 1 && (
                          <button
                            onClick={() => removeTask(index)}
                            className="p-0.5 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 dark:text-red-400 rounded transition-colors"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                <button
                  onClick={handleCreateTemplate}
                  disabled={createTemplateMutation.isPending || updateTemplateMutation.isPending}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white text-sm rounded-lg transition-colors"
                >
                  {createTemplateMutation.isPending || updateTemplateMutation.isPending
                    ? (editingTemplate ? 'Updating...' : 'Creating...')
                    : (editingTemplate ? 'Update' : 'Create')
                  }
                </button>
                <button
                  onClick={resetTemplateForm}
                  className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 text-sm rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </OnboardingModal>

          {/* Assign Onboarding Form */}
          {showAssignForm && (
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 mb-8">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Assign Onboarding to Employee
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Select Template
                  </label>
                  <select
                    value={selectedWorkflow}
                    onChange={(e) => setSelectedWorkflow(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="">Choose a template...</option>
                    {templates?.map((template: OnboardingTemplate) => (
                      <option key={template.id} value={template.id}>
                        {template.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Select Employee
                  </label>
                  <select
                    value={selectedUser}
                    onChange={(e) => setSelectedUser(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="">Choose an employee...</option>
                    {employees?.map((employee: any) => (
                      <option key={employee.id} value={employee.id}>
                        {employee.username} - {employee.role}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Select the employee to assign this onboarding workflow to.
                  </p>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={handleAssign}
                    disabled={assignWorkflowMutation.isPending}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
                  >
                    {assignWorkflowMutation.isPending ? 'Assigning...' : 'Assign Onboarding'}
                  </button>
                  <button
                    onClick={resetAssignForm}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Content based on active tab */}
          {activeTab === 'templates' ? (
            <div className="space-y-4">
              {templates?.map((template: OnboardingTemplate) => (
                <div
                  key={template.id}
                  className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                        {template.title}
                      </h3>
                      <p className="text-slate-600 dark:text-slate-400 mb-3">
                        {template.description}
                      </p>
                      <div className="flex items-center space-x-4 text-sm text-slate-500 dark:text-slate-400">
                        <span className="flex items-center space-x-1">
                          <FileText className="w-4 h-4" />
                          <span>{template.tasks.length} tasks</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" />
                          <span>{new Date(template.created_at).toLocaleDateString()}</span>
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${template.is_active
                          ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-700/50 dark:text-slate-400'
                          }`}>
                          {template.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => handleEditTemplate(template)}
                        className="p-2 bg-blue-100 text-blue-600 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 rounded-lg transition-colors"
                        title="Edit Template"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteTemplate(template.id, template.title)}
                        className="p-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 rounded-lg transition-colors"
                        title="Delete Template"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}

              {templates?.length === 0 && (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                    No templates yet
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 mb-4">
                    Create your first onboarding template to get started
                  </p>
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                  >
                    Create Template
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {assignments?.map((assignment: EmployeeAssignment) => (
                <div
                  key={assignment.id}
                  className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                          {assignment.user.username}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor(assignment.status)}`}>
                          {getStatusIcon(assignment.status)}
                          <span>{assignment.status.replace('_', ' ')}</span>
                        </span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-400 mb-3">
                        {assignment.user.email}
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                            {assignment.workflow.title}
                          </span>
                          <span className="text-sm text-slate-500 dark:text-slate-400">
                            {assignment.tasks_completed}/{assignment.tasks_total} tasks
                          </span>
                        </div>
                        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${assignment.progress_percentage}%` }}
                          />
                        </div>
                        <div className="flex items-center space-x-4 text-xs text-slate-500 dark:text-slate-400">
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-3 h-3" />
                            <span>Started: {new Date(assignment.started_at).toLocaleDateString()}</span>
                          </span>
                          {assignment.completed_at && (
                            <span className="flex items-center space-x-1">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Completed: {new Date(assignment.completed_at).toLocaleDateString()}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      <button
                        onClick={() => setSelectedAssignment(assignment)}
                        className="p-2 bg-indigo-100 text-indigo-600 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 rounded-lg transition-colors"
                        title="View Details"
                      >
                        <BarChart3 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}

              {assignments?.length === 0 && (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
                    No assignments yet
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 mb-4">
                    Assign onboarding templates to employees to get started
                  </p>
                  <button
                    onClick={() => setShowAssignForm(true)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                  >
                    Assign Onboarding
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Assignment Details Modal */}
          {selectedAssignment && (
            <OnboardingModal
              isOpen={true}
              onClose={() => setSelectedAssignment(null)}
              title={`${selectedAssignment.user.username}'s Onboarding Progress`}
            >
              <div className="space-y-6">
                {/* Employee Profile Card */}
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-xl p-4 border border-indigo-200 dark:border-indigo-800">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center">
                      <Users className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                        {selectedAssignment.user.username}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {selectedAssignment.user.email}
                      </p>
                      <div className="flex items-center space-x-3 mt-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor(selectedAssignment.status)}`}>
                          {getStatusIcon(selectedAssignment.status)}
                          <span>{selectedAssignment.status.replace('_', ' ')}</span>
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          Active for {Math.floor((Date.now() - new Date(selectedAssignment.started_at).getTime()) / (1000 * 60 * 60 * 24))} days
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Enhanced Progress Overview */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-slate-900 dark:text-white">Overall Progress</h4>
                      <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                        {selectedAssignment.progress_percentage}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 mb-2">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${selectedAssignment.progress_percentage}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                      <span>{selectedAssignment.tasks_completed} completed</span>
                      <span>{selectedAssignment.tasks_total - selectedAssignment.tasks_completed} remaining</span>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-slate-900 dark:text-white">Time Tracking</h4>
                      <Clock className="w-4 h-4 text-slate-400" />
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Started:</span>
                        <span className="text-slate-900 dark:text-white">
                          {new Date(selectedAssignment.started_at).toLocaleDateString()}
                        </span>
                      </div>
                      {selectedAssignment.completed_at && (
                        <div className="flex justify-between">
                          <span className="text-slate-600 dark:text-slate-400">Completed:</span>
                          <span className="text-slate-900 dark:text-white">
                            {new Date(selectedAssignment.completed_at).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Avg. per task:</span>
                        <span className="text-slate-900 dark:text-white">
                          {selectedAssignment.tasks_completed > 0 
                            ? `${Math.floor((Date.now() - new Date(selectedAssignment.started_at).getTime()) / (1000 * 60 * 60 * 24) / selectedAssignment.tasks_completed)} days`
                            : 'N/A'
                          }
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Workflow Information */}
                <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-slate-900 dark:text-white">Assigned Workflow</h4>
                    <FileText className="w-4 h-4 text-slate-400" />
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                    <h5 className="font-medium text-slate-900 dark:text-white mb-1">
                      {selectedAssignment.workflow.title}
                    </h5>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {selectedAssignment.workflow.description || 'No description available'}
                    </p>
                    <div className="flex items-center space-x-4 mt-2 text-xs text-slate-500 dark:text-slate-400">
                      <span>📋 {selectedAssignment.tasks_total} tasks</span>
                      <span>⏱️ Est. {selectedAssignment.tasks_total * 2} days</span>
                      <span>🎯 {selectedAssignment.workflow?.tasks?.filter((task: any) => task.is_required).length || 0} required</span>
                    </div>
                  </div>
                </div>

                {/* Dynamic Task Breakdown */}
                <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-slate-900 dark:text-white">Task Breakdown</h4>
                    <span className="text-xs bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400 px-2 py-1 rounded-full">
                      {selectedAssignment.tasks_completed}/{selectedAssignment.tasks_total} Completed
                    </span>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                    {/* Always show tasks based on the completion count */}
                    {Array.from({ length: selectedAssignment.tasks_total || 4 }, (_, index) => {
                      const isCompleted = index < selectedAssignment.tasks_completed;
                      const isInProgress = index === selectedAssignment.tasks_completed && selectedAssignment.tasks_completed < selectedAssignment.tasks_total;
                      const status = isCompleted ? 'completed' : isInProgress ? 'in_progress' : 'pending';
                      
                      return (
                        <div key={index} className="flex items-center space-x-3 p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
                          <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                            status === 'completed' ? 'bg-green-500' : 
                            status === 'in_progress' ? 'bg-blue-500' : 'bg-slate-300'
                          }`}>
                            {status === 'completed' && <CheckCircle2 className="w-2 h-2 text-white" />}
                            {status === 'in_progress' && <Clock className="w-2 h-2 text-white" />}
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-slate-900 dark:text-white">
                              Task {index + 1}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                              {isCompleted ? 'Completed' : isInProgress ? 'In Progress' : 'Pending'}
                            </p>
                            {isCompleted && (
                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Completed {new Date(selectedAssignment.started_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 px-2 py-1 rounded-full">
                              Required
                            </span>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              status === 'completed' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' :
                              status === 'in_progress' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' :
                              'bg-slate-100 text-slate-600 dark:bg-slate-700/50 dark:text-slate-400'
                            }`}>
                              {status.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-center space-x-3 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <button
                    onClick={handleSendReminder}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition-colors flex items-center space-x-2"
                  >
                    <span>📧</span>
                    <span>Send Reminder</span>
                  </button>
                  <button
                    onClick={() => setShowNoteModal(true)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 text-sm rounded-lg transition-colors flex items-center space-x-2"
                  >
                    <span>📝</span>
                    <span>Add Note</span>
                  </button>
                  <button
                    onClick={() => setSelectedAssignment(null)}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 text-sm rounded-lg transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </OnboardingModal>
          )}

          {/* Add Note Modal */}
          {showNoteModal && selectedAssignment && (
            <OnboardingModal
              isOpen={true}
              onClose={() => {
                setShowNoteModal(false)
                setNoteText('')
              }}
              title={`Add Note for ${selectedAssignment.user.username}`}
            >
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Note
                  </label>
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Add a note about this employee's onboarding progress..."
                    rows={4}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                  />
                </div>
                
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={handleAddNote}
                    disabled={!noteText.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white text-sm rounded-lg transition-colors"
                  >
                    Add Note
                  </button>
                  <button
                    onClick={() => {
                      setShowNoteModal(false)
                      setNoteText('')
                    }}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 text-sm rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </OnboardingModal>
          )}

          {/* Delete Confirmation Modal */}
          {deleteConfirmation && (
            <OnboardingModal
              isOpen={true}
              onClose={() => setDeleteConfirmation(null)}
              title=""
            >
              <div className="text-center py-2">
                {/* Compact Warning Icon */}
                <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Trash2 className="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                
                {/* Clean Title */}
                <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-2">
                  Delete "{deleteConfirmation.title}"?
                </h3>
                
                {/* Compact Warning */}
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  This action cannot be undone and will remove all related assignments.
                </p>

                {/* Clean Button Layout */}
                <div className="flex justify-center space-x-2">
                  <button
                    onClick={confirmDelete}
                    disabled={deleteTemplateMutation.isPending}
                    className="px-4 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white text-sm rounded-lg transition-colors"
                  >
                    {deleteTemplateMutation.isPending ? 'Deleting...' : 'Delete'}
                  </button>
                  <button
                    onClick={() => setDeleteConfirmation(null)}
                    className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 text-sm rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </OnboardingModal>
          )}
        </div>
      </Container>
    </div>
  )
}
