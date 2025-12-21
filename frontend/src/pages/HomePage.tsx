export function HomePage() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to Surgical Outcomes Database
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          Track and analyze patient surgery outcomes with ease
        </p>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 max-w-4xl mx-auto">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900">Patients</h3>
              <p className="mt-1 text-sm text-gray-500">
                Manage patient records and demographics
              </p>
            </div>
          </div>
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900">Surgeries</h3>
              <p className="mt-1 text-sm text-gray-500">
                Record surgery details and outcomes
              </p>
            </div>
          </div>
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium text-gray-900">Reports</h3>
              <p className="mt-1 text-sm text-gray-500">
                Generate analytics and insights
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
