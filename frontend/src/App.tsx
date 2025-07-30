
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { BarChart3, Home, Settings as SettingsIcon, Search, Shield, Upload as UploadIcon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import SearchResults from './pages/SearchResults';
import AnalysisDetail from './pages/AnalysisDetail';
import Settings from './pages/Settings';

// ホームページコンポーネント
const HomePage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-600 mb-2">
            Fujisan
          </h1>
          <p className="text-gray-600">
            アプリケーション画像不正利用検出システム
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
                  PostgreSQL 15 + Redis<br />
                  脅威度スコアリングシステム
                </p>
              </div>
              <div className="p-4 bg-secondary-50 rounded-lg">
                <h3 className="text-lg font-medium text-secondary-700 mb-2">
                  フロントエンド
                </h3>
                <p className="text-gray-600">
                  React 18 + TypeScript<br />
                  Tailwind CSS + Recharts<br />
                  リアルタイムダッシュボード
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 text-center">
            <Link
              to="/dashboard"
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200 inline-flex items-center space-x-2"
            >
              <BarChart3 className="w-4 h-4" />
              <span>ダッシュボードを開く</span>
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
};

// ナビゲーションコンポーネント
const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'ホーム', icon: Home },
    { path: '/dashboard', label: 'ダッシュボード', icon: BarChart3 },
    { path: '/upload', label: '画像アップロード', icon: UploadIcon },
    { path: '/search', label: '画像検索', icon: Search },
    { path: '/analysis', label: '脅威分析', icon: Shield },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="text-xl font-bold text-primary-600">
                ABDS
              </Link>
            </div>
            <div className="ml-6 flex space-x-8">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors ${
                      isActive(item.path)
                        ? 'text-primary-600 border-b-2 border-primary-600'
                        : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

// 404ページ
const NotFound = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-gray-600 mb-4">お探しのページが見つかりません</p>
        <Link
          to="/"
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          ホームに戻る
        </Link>
      </div>
    </div>
  );
};

// レイアウトコンポーネント
const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const showNavigation = location.pathname !== '/';

  return (
    <div className="min-h-screen bg-gray-50">
      {showNavigation && <Navigation />}
      {children}
    </div>
  );
};

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/search-results" element={<SearchResults />} />
          <Route path="/search-results/:analysisId" element={<AnalysisDetail />} />
          <Route path="/analysis/:analysisId" element={<AnalysisDetail />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/search" element={<div className="p-8 text-center text-gray-500">画像検索機能（開発中）</div>} />
          <Route path="/analysis" element={<div className="p-8 text-center text-gray-500">脅威分析機能（開発中）</div>} />
          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App