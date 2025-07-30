import React from 'react';
import { format } from 'date-fns';
import {
  Search,
  Shield,
  Clock,
  Image,
  AlertTriangle,
  TrendingUp,
  Eye,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';

import StatsCard from '../components/StatsCard';
import { useDashboardData } from '../hooks/useDashboardData';
import type { RecentDetection } from '../hooks/useDashboardData';

// 脅威レベル別の色設定
const THREAT_COLORS = {
  SAFE: '#10b981',
  LOW: '#f59e0b',
  MEDIUM: '#f97316',
  HIGH: '#ef4444',
  UNKNOWN: '#6b7280',
};

const Dashboard: React.FC = () => {
  const {
    stats,
    threatDistribution,
    dailyDetections,
    recentDetections,
    isLoading,
    isError,
    error,
    refetch,
  } = useDashboardData();

  // エラー状態の処理
  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            データの読み込みに失敗しました
          </h2>
          <p className="text-gray-600 mb-4">
            {error instanceof Error ? error.message : 'ネットワークエラーが発生しました'}
          </p>
          <button
            onClick={() => refetch()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            再試行
          </button>
        </div>
      </div>
    );
  }

  // 脅威分布データをPieChart用に変換
  const threatDistributionData = threatDistribution ? [
    { name: '安全', value: threatDistribution.SAFE, color: THREAT_COLORS.SAFE },
    { name: '低リスク', value: threatDistribution.LOW, color: THREAT_COLORS.LOW },
    { name: '中リスク', value: threatDistribution.MEDIUM, color: THREAT_COLORS.MEDIUM },
    { name: '高リスク', value: threatDistribution.HIGH, color: THREAT_COLORS.HIGH },
    { name: '不明', value: threatDistribution.UNKNOWN, color: THREAT_COLORS.UNKNOWN },
  ] : [];

  // 日別データをグラフ用に変換
  const dailyChartData = dailyDetections?.map(day => ({
    date: format(new Date(day.date), 'M/d'),
    総検査数: day.totalScans,
    脅威検出数: day.threatDetections,
    安全: day.safeDetections,
    低リスク: day.lowRisk,
    中リスク: day.mediumRisk,
    高リスク: day.highRisk,
  })) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
              <p className="text-gray-600 mt-1">
                ABDSシステムの監視状況と統計情報
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span>更新</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="本日の検査数"
            value={stats?.todayScans || 0}
            icon={Search}
            color="blue"
            description="今日実行された検査"
            trend={stats?.trends ? {
              value: stats.trends.scansChange,
              isPositive: stats.trends.scansChange > 0
            } : undefined}
            loading={isLoading}
          />

          <StatsCard
            title="脅威検出数"
            value={stats?.threatDetections || 0}
            icon={Shield}
            color="red"
            description="検出された脅威"
            trend={stats?.trends ? {
              value: stats.trends.threatsChange,
              isPositive: stats.trends.threatsChange < 0 // 脅威は少ない方が良い
            } : undefined}
            loading={isLoading}
          />

          <StatsCard
            title="処理中のタスク"
            value={stats?.processingTasks || 0}
            icon={Clock}
            color="yellow"
            description="実行中の処理"
            trend={stats?.trends ? {
              value: stats.trends.tasksChange,
              isPositive: stats.trends.tasksChange < 0 // タスクは少ない方が良い
            } : undefined}
            loading={isLoading}
          />

          <StatsCard
            title="総画像数"
            value={stats?.totalImages || 0}
            icon={Image}
            color="green"
            description="これまでに検査した画像"
            loading={isLoading}
          />
        </div>

        {/* グラフセクション */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* 脅威レベル分布 */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              脅威レベル分布
            </h3>
            {isLoading ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={threatDistributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {threatDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* 日別検出数推移 */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              日別検出数推移（過去7日）
            </h3>
            {isLoading ? (
              <div className="h-64 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="総検査数"
                    stroke="#3b82f6"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="脅威検出数"
                    stroke="#ef4444"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* 脅威レベル別詳細グラフ */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            脅威レベル別検出数推移
          </h3>
          {isLoading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="安全" stackId="a" fill={THREAT_COLORS.SAFE} />
                <Bar dataKey="低リスク" stackId="a" fill={THREAT_COLORS.LOW} />
                <Bar dataKey="中リスク" stackId="a" fill={THREAT_COLORS.MEDIUM} />
                <Bar dataKey="高リスク" stackId="a" fill={THREAT_COLORS.HIGH} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* 最近の検出一覧 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">最近の検出</h3>
          </div>

          {isLoading ? (
            <div className="p-6">
              <div className="animate-pulse space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-4">
                    <div className="w-4 h-4 bg-gray-200 rounded"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {recentDetections?.map((detection) => (
                <DetectionItem key={detection.id} detection={detection} />
              ))}

              {(!recentDetections || recentDetections.length === 0) && (
                <div className="p-6 text-center text-gray-500">
                  検出データがありません
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// 検出アイテムコンポーネント
const DetectionItem: React.FC<{ detection: RecentDetection }> = ({ detection }) => {
  const getThreatColor = (level: string) => {
    switch (level) {
      case 'HIGH': return 'bg-red-100 text-red-800';
      case 'MEDIUM': return 'bg-orange-100 text-orange-800';
      case 'LOW': return 'bg-yellow-100 text-yellow-800';
      case 'SAFE': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'bg-green-100 text-green-800';
      case 'PROCESSING': return 'bg-blue-100 text-blue-800';
      case 'FAILED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-3">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getThreatColor(detection.threatLevel)}`}>
              {detection.threatLevel}
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(detection.status)}`}>
              {detection.status === 'PROCESSING' ? '処理中' :
               detection.status === 'COMPLETED' ? '完了' : '失敗'}
            </span>
            <span className="text-sm font-medium text-gray-900">
              スコア: {detection.threatScore.toFixed(1)}
            </span>
          </div>

          <div className="mt-2">
            <div className="flex items-center space-x-2">
              <a
                href={detection.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 flex items-center space-x-1"
              >
                <span className="truncate max-w-md">{detection.url}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
                          </div>

              <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                <span>ドメイン: {detection.domain}</span>
                <span>検出日時: {format(new Date(detection.detectedAt), 'yyyy/MM/dd HH:mm')}</span>
              </div>

            {detection.riskFactors.length > 0 && (
              <div className="mt-2">
                <div className="flex flex-wrap gap-1">
                  {detection.riskFactors.map((factor, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded text-xs bg-red-50 text-red-700"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="ml-4 flex items-center space-x-2">
          <button className="text-gray-400 hover:text-gray-500">
            <Eye className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;