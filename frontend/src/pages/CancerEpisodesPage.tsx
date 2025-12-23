import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { CancerEpisodeForm } from '../components/CancerEpisodeForm'
import { CancerEpisodeDetailModal } from '../components/CancerEpisodeDetailModal'
import { formatDate, formatCancerType } from '../utils/formatters'
import api from '../services/api'

interface Episode {
  episode_id: string
  patient_id: string
  condition_type: string
  cancer_type: string
  referral_date: string
  first_seen_date: string
  lead_clinician: string
  episode_status: string
  cancer_data: any
}

export function CancerEpisodesPage() {
  const navigate = useNavigate()
  const [episodes, setEpisodes] = useState<Episode[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [cancerTypeFilter, setCancerTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadEpisodes = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get('/episodes/')
      setEpisodes(response.data)
      setError('')
    } catch (err: any) {
      console.error('Failed to load episodes:', err)
      setError('Failed to load episodes')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadEpisodes()
  }, [loadEpisodes])

  const filteredEpisodes = useMemo(() => {
    return episodes.filter(episode => {
      const matchesSearch = !searchTerm || 
        episode.episode_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        episode.patient_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        episode.lead_clinician?.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesCancerType = !cancerTypeFilter || episode.cancer_type === cancerTypeFilter
      const matchesStatus = !statusFilter || episode.episode_status === statusFilter

      return matchesSearch && matchesCancerType && matchesStatus
    })
  }, [episodes, searchTerm, cancerTypeFilter, statusFilter])

  const handleCreate = async (data: any) => {
    try {
      await api.post('/episodes/', data)
      setShowForm(false)
      setSelectedEpisode(null)
      setEditMode(false)
      loadEpisodes()
      setSuccess('Episode created successfully')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      console.error('Failed to create episode:', err)
      setError(err.response?.data?.detail || 'Failed to create episode')
      setTimeout(() => setError(''), 5000)
    }
  }

  const handleEdit = async (data: any) => {
    if (!selectedEpisode) return
    
    try {
      await api.put(`/episodes/${selectedEpisode.episode_id}`, data)
      setShowForm(false)
      setSelectedEpisode(null)
      setEditMode(false)
      loadEpisodes()
      setSuccess('Episode updated successfully')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      console.error('Failed to update episode:', err)
      setError(err.response?.data?.detail || 'Failed to update episode')
      setTimeout(() => setError(''), 5000)
    }
  }

  const handleDelete = async (episodeId: string) => {
    if (!confirm('Are you sure you want to delete this episode?')) return
    
    try {
      await api.delete(`/episodes/${episodeId}`)
      loadEpisodes()
      setSuccess('Episode deleted successfully')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      console.error('Failed to delete episode:', err)
      setError(err.response?.data?.detail || 'Failed to delete episode')
      setTimeout(() => setError(''), 5000)
    }
  }

  const handleViewDetails = (episode: Episode) => {
    setSelectedEpisode(episode)
    setShowDetailModal(true)
  }

  const handleEditClick = (episode: Episode) => {
    setSelectedEpisode(episode)
    setEditMode(true)
    setShowForm(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'completed': return 'bg-blue-100 text-blue-800'
      case 'cancelled': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cancer Episodes"
        subtitle="Manage cancer care episodes and treatments"
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        }
        action={
          !showForm && (
            <Button variant="primary" onClick={() => {
              setSelectedEpisode(null)
              setEditMode(false)
              setShowForm(true)
            }}>
              + Add Episode
            </Button>
          )
        }
      />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {success}
        </div>
      )}

      {showForm ? (
        <Card>
          <CancerEpisodeForm
            mode={editMode ? 'edit' : 'create'}
            initialData={selectedEpisode}
            onSubmit={editMode ? handleEdit : handleCreate}
            onCancel={() => {
              setShowForm(false)
              setSelectedEpisode(null)
              setEditMode(false)
            }}
          />
        </Card>
      ) : (
        <>
          {/* Filters */}
          <Card>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                <input
                  type="text"
                  placeholder="Episode ID, Patient ID, Clinician..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cancer Type</label>
                <select
                  value={cancerTypeFilter}
                  onChange={(e) => setCancerTypeFilter(e.target.value)}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Types</option>
                  <option value="bowel">Bowel (Colorectal)</option>
                  <option value="kidney">Kidney (Renal)</option>
                  <option value="breast_primary">Breast (Primary)</option>
                  <option value="breast_metastatic">Breast (Metastatic)</option>
                  <option value="oesophageal">Oesophageal</option>
                  <option value="ovarian">Ovarian</option>
                  <option value="prostate">Prostate</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full h-10 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div className="flex items-end">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSearchTerm('')
                    setCancerTypeFilter('')
                    setStatusFilter('')
                  }}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </Card>

          {/* Episodes Table */}
          <Card>
            {loading ? (
              <div className="text-center py-12 text-gray-500">Loading episodes...</div>
            ) : filteredEpisodes.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No episodes found. {searchTerm || cancerTypeFilter || statusFilter ? 'Try adjusting your filters.' : 'Click "+ Add Episode" to create one.'}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Episode ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Patient
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cancer Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Referral Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Lead Clinician
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredEpisodes.map((episode) => (
                      <tr key={episode.episode_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => handleViewDetails(episode)}
                            className="text-sm font-medium text-blue-600 hover:text-blue-800"
                          >
                            {episode.episode_id}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {episode.patient_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCancerType(episode.cancer_type)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(episode.referral_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {episode.lead_clinician || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(episode.episode_status)}`}>
                            {episode.episode_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                          <Button
                            size="small"
                            variant="secondary"
                            onClick={() => handleViewDetails(episode)}
                          >
                            View
                          </Button>
                          <Button
                            size="small"
                            variant="secondary"
                            onClick={() => handleEditClick(episode)}
                          >
                            Edit
                          </Button>
                          <Button
                            size="small"
                            variant="danger"
                            onClick={() => handleDelete(episode.episode_id)}
                          >
                            Delete
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedEpisode && (
        <CancerEpisodeDetailModal
          episode={selectedEpisode}
          onClose={() => {
            setShowDetailModal(false)
            setSelectedEpisode(null)
          }}
          onEdit={() => {
            setShowDetailModal(false)
            handleEditClick(selectedEpisode)
          }}
        />
      )}
    </div>
  )
}
