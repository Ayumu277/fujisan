import React from 'react';
import { format } from 'date-fns';
import {
  ExternalLink,
  Shield,
  AlertTriangle,
  CheckCircle,
  Info,
  Eye,
  Calendar,
  Globe,
  TrendingUp,
  Clock,
} from 'lucide-react';

// 検索結果の型定義
export interface SearchResult {
  id: string;
  imageId: string;
  foundUrl: string;
  domain: string;
  title?: string;
  description?: string;
  thumbnailUrl?: string;
  similarityScore: number;
  threatLevel: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  threatScore: number;
  isOfficial: boolean;
  detectedAt: string;
  lastChecked: string;
  status: 'ACTIVE' | 'REMOVED' | 'INVESTIGATING';
  riskFactors: string[];
  metadata?: {
    pageTitle?: string;
    metaDescription?: string;
    lastModified?: string;
    language?: string;
    socialShares?: number;
  };
  aiAnalysis?: {
    contentAbuse: number;
    copyrightRisk: number;
    commercialUse: boolean;
    unauthorizedRepost: boolean;
  };
}

interface ResultCardProps {
  result: SearchResult;
  onViewDetails: (result: SearchResult) => void;
  onViewOriginal: (url: string) => void;
  compact?: boolean;
  className?: string;
}

export const ResultCard: React.FC<ResultCardProps> = ({
  result,
  onViewDetails,
  onViewOriginal,
  compact = false,
  className = '',
}) => {
  // 脅威レベルの色とアイコンを取得
  const getThreatConfig = (level: string) => {
    switch (level) {
      case 'HIGH':
        return {
          color: 'bg-red-100 text-red-800 border-red-200',
          iconColor: 'text-red-600',
          icon: AlertTriangle,
          label: '高リスク',
          bgGradient: 'bg-gradient-to-br from-red-50 to-red-100',
        };
      case 'MEDIUM':
        return {
          color: 'bg-orange-100 text-orange-800 border-orange-200',
          iconColor: 'text-orange-600',
          icon: Shield,
          label: '中リスク',
          bgGradient: 'bg-gradient-to-br from-orange-50 to-orange-100',
        };
      case 'LOW':
        return {
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          iconColor: 'text-yellow-600',
          icon: Info,
          label: '低リスク',
          bgGradient: 'bg-gradient-to-br from-yellow-50 to-yellow-100',
        };
      case 'SAFE':
        return {
          color: 'bg-green-100 text-green-800 border-green-200',
          iconColor: 'text-green-600',
          icon: CheckCircle,
          label: '安全',
          bgGradient: 'bg-gradient-to-br from-green-50 to-green-100',
        };
      default:
        return {
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          iconColor: 'text-gray-600',
          icon: Info,
          label: '不明',
          bgGradient: 'bg-gradient-to-br from-gray-50 to-gray-100',
        };
    }
  };

  // ステータスの表示設定
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return { color: 'bg-blue-100 text-blue-800', label: 'アクティブ' };
      case 'REMOVED':
        return { color: 'bg-gray-100 text-gray-800', label: '削除済み' };
      case 'INVESTIGATING':
        return { color: 'bg-purple-100 text-purple-800', label: '調査中' };
      default:
        return { color: 'bg-gray-100 text-gray-800', label: '不明' };
    }
  };

  const threatConfig = getThreatConfig(result.threatLevel);
  const statusConfig = getStatusConfig(result.status);
  const ThreatIcon = threatConfig.icon;

  // 類似度に基づく進捗バーの色
  const getSimilarityColor = (score: number) => {
    if (score >= 90) return 'bg-red-500';
    if (score >= 70) return 'bg-orange-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 ${className}`}>
      {/* ヘッダー部分 */}
      <div className={`p-4 ${threatConfig.bgGradient} border-b border-gray-200`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${threatConfig.color} border`}>
              <ThreatIcon className={`w-5 h-5 ${threatConfig.iconColor}`} />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${threatConfig.color} border`}>
                  {threatConfig.label}
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
                {result.isOfficial && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    公式
                  </span>
                )}
              </div>
              <div className="mt-1 flex items-center space-x-4 text-sm text-gray-600">
                <span className="font-semibold">スコア: {result.threatScore.toFixed(1)}</span>
                <span>類似度: {result.similarityScore.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onViewDetails(result)}
              className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
              title="詳細を表示"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => onViewOriginal(result.foundUrl)}
              className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
              title="元のページを開く"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="p-4">
        {!compact && (
          <>
            {/* サムネイルとURL情報 */}
            <div className="flex space-x-4 mb-4">
              {result.thumbnailUrl && (
                <div className="flex-shrink-0 w-24 h-24 bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    src={result.thumbnailUrl}
                    alt="Thumbnail"
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                  {result.title || result.metadata?.pageTitle || 'タイトルなし'}
                </h3>
                <div className="flex items-center space-x-2 text-sm text-gray-600 mb-2">
                  <Globe className="w-4 h-4" />
                  <a
                    href={result.foundUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 truncate"
                  >
                    {result.domain}
                  </a>
                </div>
                {(result.description || result.metadata?.metaDescription) && (
                  <p className="text-sm text-gray-600 line-clamp-2">
                    {result.description || result.metadata?.metaDescription}
                  </p>
                )}
              </div>
            </div>

            {/* 類似度バー */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                <span>画像類似度</span>
                <span className="font-medium">{result.similarityScore.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getSimilarityColor(result.similarityScore)}`}
                  style={{ width: `${result.similarityScore}%` }}
                />
              </div>
            </div>
          </>
        )}

        {/* リスク要因 */}
        {result.riskFactors.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">リスク要因</h4>
            <div className="flex flex-wrap gap-1">
              {result.riskFactors.slice(0, compact ? 3 : 5).map((factor, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded text-xs bg-red-50 text-red-700 border border-red-200"
                >
                  {factor}
                </span>
              ))}
              {result.riskFactors.length > (compact ? 3 : 5) && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-50 text-gray-700">
                  +{result.riskFactors.length - (compact ? 3 : 5)}個
                </span>
              )}
            </div>
          </div>
        )}

        {/* AI分析結果 */}
        {result.aiAnalysis && !compact && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">AI分析</h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">コンテンツ悪用</span>
                <span className={`font-medium ${result.aiAnalysis.contentAbuse > 70 ? 'text-red-600' : 'text-green-600'}`}>
                  {result.aiAnalysis.contentAbuse.toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">著作権リスク</span>
                <span className={`font-medium ${result.aiAnalysis.copyrightRisk > 70 ? 'text-red-600' : 'text-green-600'}`}>
                  {result.aiAnalysis.copyrightRisk.toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">商用利用</span>
                <span className={`font-medium ${result.aiAnalysis.commercialUse ? 'text-red-600' : 'text-green-600'}`}>
                  {result.aiAnalysis.commercialUse ? 'あり' : 'なし'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">無許可転載</span>
                <span className={`font-medium ${result.aiAnalysis.unauthorizedRepost ? 'text-red-600' : 'text-green-600'}`}>
                  {result.aiAnalysis.unauthorizedRepost ? 'あり' : 'なし'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* フッター情報 */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-100">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Calendar className="w-3 h-3" />
              <span>検出: {format(new Date(result.detectedAt), 'yyyy/MM/dd')}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>更新: {format(new Date(result.lastChecked), 'MM/dd HH:mm')}</span>
            </div>
          </div>
          
          {result.metadata?.socialShares && (
            <div className="flex items-center space-x-1">
              <TrendingUp className="w-3 h-3" />
              <span>{result.metadata.socialShares} シェア</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultCard; 