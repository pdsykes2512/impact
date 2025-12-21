import { PageHeader } from '../components/PageHeader'
import { Card } from '../components/Card'

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports & Analytics"
        subtitle="View comprehensive surgical outcomes and performance metrics"
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card hover>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">—</div>
            <div className="text-sm text-gray-500">Total Procedures</div>
          </div>
        </Card>
        <Card hover>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">—%</div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </Card>
        <Card hover>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">—</div>
            <div className="text-sm text-gray-500">Average Duration</div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="text-center py-12">
          <svg className="mx-auto w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-500">Reports will be generated once surgery records are added to the system</p>
        </div>
      </Card>
    </div>
  )
}
