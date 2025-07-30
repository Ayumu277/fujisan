
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-600 mb-2">
            ABDSシステム
          </h1>
          <p className="text-gray-600">
            アプリケーション管理システム
          </p>
        </header>

        <main className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              システム概要
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 bg-primary-50 rounded-lg">
                <h3 className="text-lg font-medium text-primary-700 mb-2">
                  バックエンド
                </h3>
                <p className="text-gray-600">
                  FastAPI + Python 3.11<br />
                  PostgreSQL 15 + Redis
                </p>
              </div>
              <div className="p-4 bg-secondary-50 rounded-lg">
                <h3 className="text-lg font-medium text-secondary-700 mb-2">
                  フロントエンド
                </h3>
                <p className="text-gray-600">
                  React 18 + TypeScript<br />
                  Tailwind CSS
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 text-center">
            <button className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
              開始する
            </button>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App