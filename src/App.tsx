import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

// 基本的なページコンポーネント
const HomePage = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          ABDSシステム
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          React + TypeScript + Tailwind CSS + FastAPI
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-12">
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🚀 FastAPI Backend
            </h3>
            <p className="text-gray-600">
              高性能なPython WebAPIフレームワーク
            </p>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              ⚛️ React Frontend
            </h3>
            <p className="text-gray-600">
              モダンなReactアプリケーション
            </p>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🎨 Tailwind CSS
            </h3>
            <p className="text-gray-600">
              ユーティリティファーストCSS
            </p>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              📊 React Query
            </h3>
            <p className="text-gray-600">
              強力なデータフェッチライブラリ
            </p>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🔄 Hot Reload
            </h3>
            <p className="text-gray-600">
              開発時の自動リロード対応
            </p>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🐳 Docker
            </h3>
            <p className="text-gray-600">
              コンテナ化されたデプロイ
            </p>
          </div>
        </div>

        <div className="mt-12">
          <button className="btn btn-primary px-8 py-3 text-lg">
            開始する
          </button>
        </div>
      </div>
    </div>
  </div>
)

const AboutPage = () => (
  <div className="min-h-screen bg-gray-50 py-16">
    <div className="container mx-auto px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">About</h1>
        <div className="card p-8">
          <p className="text-lg text-gray-700 leading-relaxed">
            ABDSシステムは、FastAPIとReactを使用したモダンなWebアプリケーションです。
            Docker Composeを使用して、開発環境から本番環境まで一貫したデプロイメントを提供します。
          </p>
        </div>
      </div>
    </div>
  </div>
)

const NotFoundPage = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
      <p className="text-xl text-gray-600 mb-8">ページが見つかりません</p>
      <button
        className="btn btn-primary"
        onClick={() => window.history.back()}
      >
        戻る
      </button>
    </div>
  </div>
)

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App