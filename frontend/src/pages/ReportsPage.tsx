import { useState, useEffect } from 'react'
import { PageHeader } from '../components/PageHeader'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import { apiService } from '../services/api'

interface SummaryReport {
  total_episodes: number
  episodes_with_treatments: number
  cancer_type_breakdown: Record<string, number>
  status_breakdown: Record<string, number>
}

interface ClinicianPerformance {
  _id: string
  total_episodes: number
  cancer_types: string[]
}

interface FieldStat {
  field: string
  category: string
  complete_count: number
  total_count: number
  completeness: number
  missing_count: number
}

interface CategoryStat {
  name: string
  total_fields: number
  avg_completeness: number
  fields: FieldStat[]
}

interface DataQualityReport {
  total_episodes: number
  total_treatments: number
  total_tumours: number
  overall_completeness: number
  categories: CategoryStat[]
}

type Tab = 'outcomes' | 'quality'

export function ReportsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('outcomes')
  const [summary, setSummary] = useState<SummaryReport | null>(null)
  const [clinicianPerf, setClinicianPerf] = useState<ClinicianPerformance[]>([])
  const [dataQuality, setDataQuality] = useState<DataQualityReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadReports()
  }, [activeTab])

  const loadReports = async () => {
    try {
      setLoading(true)
      if (activeTab === 'outcomes') {
        const [summaryRes, clinicianRes] = await Promise.all([
          apiService.reports.summary(),
          apiService.reports.surgeonPerformance()
        ])
        setSummary(summaryRes.data)
        setClinicianPerf(clinicianRes.data.surgeons || [])
      } else {
        const response = await fetch('http://localhost:8000/api/reports/data-quality', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        setDataQuality(data)
      }
    } catch (error) {
      console.error('Failed to load reports:', error)
    } finally {
      setLoading(false)
    }
  }

  const downloadExcel = async (endpoint: string, filename: string) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to download')
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download Excel:', error)
      alert('Failed to download report. Please try again.')
    }
  }

  // For data quality: higher is better
  const getCompletenessColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600 bg-green-100'
    if (percentage >= 70) return 'text-yellow-600 bg-yellow-100'
    if (percentage >= 50) return 'text-orange-600 bg-orange-100'
    return 'text-red-600 bg-red-100'
  }

  const getCompletenessBarColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-green-500'
    if (percentage >= 70) return 'bg-yellow-500'
    if (percentage >= 50) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getCompletenessCardColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-green-50 border-green-200'
    if (percentage >= 70) return 'bg-yellow-50 border-yellow-200'
    if (percentage >= 50) return 'bg-orange-50 border-orange-200'
    return 'bg-red-50 border-red-200'
  }

  const getCompletenessTextColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600'
    if (percentage >= 70) return 'text-yellow-600'
    if (percentage >= 50) return 'text-orange-600'
    return 'text-red-600'
  }

  // For outcomes: lower is better (inverse of data quality)
  const getOutcomeColor = (rate: number) => {
    const percentage = rate * 100
    if (percentage <= 5) return 'text-green-600 bg-green-100'
    if (percentage <= 10) return 'text-yellow-600 bg-yellow-100'
    if (percentage <= 20) return 'text-orange-600 bg-orange-100'
    return 'text-red-600 bg-red-100'
  }

  const getOutcomeCardColor = (rate: number) => {
    const percentage = rate * 100
    if (percentage <= 5) return 'bg-green-50 border-green-200'
    if (percentage <= 10) return 'bg-yellow-50 border-yellow-200'
    if (percentage <= 20) return 'bg-orange-50 border-orange-200'
    return 'bg-red-50 border-red-200'
  }

  const getOutcomeTextColor = (rate: number) => {
    const percentage = rate * 100
    if (percentage <= 5) return 'text-green-600'
    if (percentage <= 10) return 'text-yellow-600'
    if (percentage <= 20) return 'text-orange-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Reports & Analytics" />

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('outcomes')}
            className={`${
              activeTab === 'outcomes'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            Cancer Episodes
          </button>
          <button
            onClick={() => setActiveTab('quality')}
            className={`${
              activeTab === 'quality'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            Data Quality
          </button>
        </nav>
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading reports...</p>
        </div>
      )}

      {/* Outcomes Tab */}
      {!loading && activeTab === 'outcomes' && summary && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Episodes</h3>
              <p className="mt-2 text-3xl font-bold text-gray-900">{summary.total_episodes}</p>
            </Card>

            <Card className="p-6">
              <h3 className="text-sm font-medium text-gray-500">Episodes with Treatments</h3>
              <p className="mt-2 text-3xl font-bold text-blue-600">{summary.episodes_with_treatments}</p>
            </Card>

            <Card className="p-6">
              <h3 className="text-sm font-medium text-gray-500">Cancer Types Tracked</h3>
              <p className="mt-2 text-3xl font-bold text-gray-900">
                {Object.keys(summary.cancer_type_breakdown || {}).length}
              </p>
            </Card>

            <Card className="p-6">
              <h3 className="text-sm font-medium text-gray-500">Active Episodes</h3>
              <p className="mt-2 text-3xl font-bold text-green-600">
                {summary.status_breakdown?.active || 0}
              </p>
            </Card>
          </div>

          {/* Urgency Breakdown */}
          {summary.urgency_breakdown && Object.keys(summary.urgency_breakdown).length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Surgery Urgency Breakdown</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(summary.urgency_breakdown).map(([urgency, count]) => (
                  <div key={urgency} className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-sm text-gray-500">{urgency}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Clinician Performance */}
          {clinicianPerf.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Clinician Performance</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Lead Clinician
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Total Episodes
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Cancer Types
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {clinicianPerf.map((clinician) => (
                      <tr key={clinician._id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {clinician._id || 'Not specified'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {clinician.total_episodes}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {clinician.cancer_types.filter(Boolean).join(', ') || 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Export Buttons */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">NBOCA Data Exports</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Button
                onClick={() => downloadExcel('/api/exports/nboca', 'nboca_export.xlsx')}
                variant="outline"
              >
                Download NBOCA Dataset
              </Button>
              <Button
                onClick={() => downloadExcel('/api/exports/cosd', 'cosd_export.xlsx')}
                variant="outline"
              >
                Download COSD Dataset
              </Button>
              <Button
                onClick={() => downloadExcel('/api/exports/monthly-summary', 'monthly_summary.xlsx')}
                variant="outline"
              >
                Download Monthly Summary
              </Button>
            </div>
          </Card>
        </>
      )}

      {/* Data Quality Tab */}
      {!loading && activeTab === 'quality' && dataQuality && (
        <>
          {/* Overall Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Episodes</h3>
              <p className="mt-2 text-3xl font-bold text-gray-900">{dataQuality.total_episodes}</p>
            </Card>

            <Card className="p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Tumours</h3>
              <p className="mt-2 text-3xl font-bold text-gray-900">{dataQuality.total_tumours}</p>
            </Card>

            <Card className={`p-6 border-2 ${getCompletenessCardColor(dataQuality.overall_completeness)}`}>
              <h3 className="text-sm font-medium text-gray-600">Overall Completeness</h3>
              <p className={`mt-2 text-3xl font-bold ${getCompletenessTextColor(dataQuality.overall_completeness)}`}>
                {dataQuality.overall_completeness.toFixed(1)}%
              </p>
            </Card>
          </div>

          {/* Category Breakdown */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-6">Data Completeness by Category</h3>
            <div className="space-y-4">
              {dataQuality.categories.map((category) => (
                <div key={category.name} className={`p-4 rounded-lg border-2 ${getCompletenessCardColor(category.avg_completeness)}`}>
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="text-base font-semibold text-gray-700">{category.name}</h4>
                    <span className={`text-lg font-bold ${getCompletenessTextColor(category.avg_completeness)}`}>
                      {category.avg_completeness.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                    <div
                      className={`h-2.5 rounded-full ${getCompletenessBarColor(category.avg_completeness)}`}
                      style={{ width: `${category.avg_completeness}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500">{category.total_fields} fields</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Episode Fields Detail */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Episode Data Fields</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Field
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Complete
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Missing
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Completeness
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dataQuality.episode_fields
                    .sort((a, b) => a.completeness - b.completeness)
                    .map((field) => (
                      <tr key={field.field}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {field.field}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {field.category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {field.complete_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {field.missing_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-semibold px-2 py-1 rounded ${getCompletenessColor(field.completeness)}`}>
                            {field.completeness.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Treatment Fields Detail */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Treatment Data Fields</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Field
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Complete
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Missing
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Completeness
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dataQuality.treatment_fields
                    .sort((a, b) => a.completeness - b.completeness)
                    .map((field) => (
                      <tr key={field.field}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {field.field}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {field.category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {field.complete_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                          {field.missing_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-semibold px-2 py-1 rounded ${getCompletenessColor(field.completeness)}`}>
                            {field.completeness.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
