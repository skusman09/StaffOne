'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import { pulseAPI } from '@/lib/api'
import { 
  ArrowLeft, 
  BarChart3, 
  Users, 
  MessageSquare, 
  TrendingUp,
  Star,
  Calendar
} from 'lucide-react'
import Container from '@/components/Container'
import Navbar from '@/components/Navbar'
import Link from 'next/link'

interface SurveyResult {
  id: number
  question: string
  is_active: boolean
  created_at: string
  updated_at: string
  response_count: number
  average_rating: number
  responses: Array<{
    id: number
    user_id: number
    rating: number
    comment: string | null
    created_at: string
    user?: {
      username: string
      email: string
    }
  }>
}

export default function SurveyAnalytics() {
  const params = useParams()
  const surveyId = parseInt(params.id as string)

  const { data: survey, isLoading } = useQuery({
    queryKey: ['surveyResults', surveyId],
    queryFn: () => pulseAPI.admin.getResults(surveyId),
    enabled: !isNaN(surveyId),
  })

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

  if (!survey) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
        <Navbar />
        <Container>
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
              Survey not found
            </h3>
            <Link 
              href="/admin/surveys"
              className="text-indigo-600 hover:text-indigo-700"
            >
              Back to Surveys
            </Link>
          </div>
        </Container>
      </div>
    )
  }

  // Calculate rating distribution
  const ratingDistribution = [1, 2, 3, 4, 5].map(rating => ({
    rating,
    count: survey.responses.filter(r => r.rating === rating).length,
    percentage: survey.responses.length > 0 
      ? (survey.responses.filter(r => r.rating === rating).length / survey.responses.length) * 100 
      : 0
  }))

  const ratingEmojis = {
    1: '😫',
    2: '😕', 
    3: '😐',
    4: '🙂',
    5: '🤩'
  }

  const ratingLabels = {
    1: 'Stressed',
    2: 'Down',
    3: 'Okay', 
    4: 'Good',
    5: 'Great'
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Navbar />
      <Container>
        <div className="py-8">
          {/* Header */}
          <div className="flex items-center space-x-4 mb-8">
            <Link 
              href="/admin/surveys"
              className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Survey Analytics
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-1">
                Detailed insights and responses
              </p>
            </div>
          </div>

          {/* Survey Overview */}
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 mb-8">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
              {survey.question}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Users className="w-4 h-4 text-indigo-600" />
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Total Responses
                  </span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {survey.response_count}
                </p>
              </div>
              
              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Star className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Average Rating
                  </span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {survey.average_rating.toFixed(1)}/5.0
                </p>
              </div>
              
              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Calendar className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Created
                  </span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {new Date(survey.created_at).toLocaleDateString()}
                </p>
              </div>
              
              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <BarChart3 className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                    Status
                  </span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {survey.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>
          </div>

          {/* Rating Distribution */}
          <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 mb-8">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Rating Distribution
            </h3>
            <div className="space-y-3">
              {ratingDistribution.map(({ rating, count, percentage }) => (
                <div key={rating} className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2 w-20">
                    <span className="text-2xl">{ratingEmojis[rating as keyof typeof ratingEmojis]}</span>
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {ratingLabels[rating as keyof typeof ratingLabels]}
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-6 overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-300 ${
                            rating <= 2 ? 'bg-red-500' : rating === 3 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-slate-600 dark:text-slate-400 w-12 text-right">
                        {count}
                      </span>
                      <span className="text-sm text-slate-500 dark:text-slate-500 w-12 text-right">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Comments */}
          {survey.responses.filter(r => r.comment).length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Comments ({survey.responses.filter(r => r.comment).length})
              </h3>
              <div className="space-y-4">
                {survey.responses
                  .filter(response => response.comment)
                  .map(response => (
                    <div key={response.id} className="border-b border-slate-200 dark:border-slate-700 pb-4 last:border-b-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-2xl">
                            {ratingEmojis[response.rating as keyof typeof ratingEmojis]}
                          </span>
                          <span className="font-medium text-slate-900 dark:text-white">
                            {response.user?.username || `User ${response.user_id}`}
                          </span>
                        </div>
                        <span className="text-sm text-slate-500 dark:text-slate-400">
                          {new Date(response.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                        {response.comment}
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </Container>
    </div>
  )
}
