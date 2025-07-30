import React, { useCallback, useState } from 'react';
import { format } from 'date-fns';
import {
  FileText,
  Download,
  Share2,
  AlertTriangle,
  Shield,
  CheckCircle,
  Info,
  Clock,
  User,
  Calendar,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import toast from 'react-hot-toast';

// 分析レポートデータの型定義
export interface AnalysisReportData {
  id: string;
  imageId: string;
  detectedUrl: string;
  domain: string;
  analyzedAt: string;
  lastUpdated: string;
  analyst: {
    id: string;
    name: string;
    email: string;
  };

  // 基本情報
  basicInfo: {
    originalImageTitle: string;
    detectedImageTitle: string;
    similarityScore: number;
    threatLevel: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
    threatScore: number;
    status: 'ACTIVE' | 'REMOVED' | 'INVESTIGATING';
    isOfficial: boolean;
  };

  // AI分析結果
  aiAnalysis: {
    contentAbuse: {
      score: number;
      confidence: number;
      evidence: string[];
      details: string;
    };
    copyrightInfringement: {
      probability: number;
      confidence: number;
      evidence: string[];
      details: string;
    };
    commercialUse: {
      detected: boolean;
      confidence: number;
      evidence: string[];
      details: string;
    };
    unauthorizedRepost: {
      detected: boolean;
      confidence: number;
      evidence: string[];
      details: string;
    };
    contentModification: {
      level: string;
      confidence: number;
      modifications: string[];
      details: string;
    };
  };

  // スコア内訳
  scoreBreakdown: {
    domainTrust: {
      score: number;
      weight: number;
      factors: string[];
    };
    contentSimilarity: {
      score: number;
      weight: number;
      factors: string[];
    };
    aiAnalysis: {
      score: number;
      weight: number;
      factors: string[];
    };
    contextualFactors: {
      score: number;
      weight: number;
      factors: string[];
    };
  };

  // リスク要因
  riskFactors: Array<{
    category: string;
    severity: 'low' | 'medium' | 'high';
    description: string;
    impact: string;
  }>;

  // 推奨アクション
  recommendations: Array<{
    priority: 'low' | 'medium' | 'high';
    action: string;
    description: string;
    timeline: string;
  }>;

  // 手動評価
  manualEvaluation?: {
    evaluatedBy: string;
    evaluatedAt: string;
    overrideScore?: number;
    overrideThreatLevel?: string;
    notes: string;
    confidence: number;
  };

  // コメント
  comments: Array<{
    id: string;
    author: string;
    content: string;
    createdAt: string;
    isInternal: boolean;
  }>;
}

interface AnalysisReportProps {
  data: AnalysisReportData;
  onExport?: (format: 'pdf' | 'csv' | 'json') => void;
  onShare?: () => void;
  className?: string;
}

export const AnalysisReport: React.FC<AnalysisReportProps> = ({
  data,
  onExport,
  onShare,
  className = '',
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['summary', 'aiAnalysis'])
  );
  const [isExporting, setIsExporting] = useState(false);

  // セクション展開/縮小
  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  }, []);

  // 脅威レベルの設定取得
  const getThreatConfig = (level: string) => {
    switch (level) {
      case 'HIGH':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          icon: AlertTriangle,
          label: '高リスク',
        };
      case 'MEDIUM':
        return {
          color: 'text-orange-600',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          icon: Shield,
          label: '中リスク',
        };
      case 'LOW':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          icon: Info,
          label: '低リスク',
        };
      case 'SAFE':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          icon: CheckCircle,
          label: '安全',
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          icon: Info,
          label: '不明',
        };
    }
  };

  // エクスポート処理
  const handleExport = useCallback(async (format: 'pdf' | 'csv' | 'json') => {
    setIsExporting(true);
    try {
      if (format === 'json') {
        // JSON エクスポート
        const jsonData = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis-report-${data.id}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else if (format === 'csv') {
        // CSV エクスポート
        const csvContent = generateCSVContent(data);
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis-report-${data.id}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        // PDF エクスポート（外部API呼び出し）
        await onExport?.(format);
      }

      toast.success(`レポートを${format.toUpperCase()}形式でエクスポートしました`);
    } catch (error) {
      toast.error('エクスポートに失敗しました');
      console.error('Export error:', error);
    } finally {
      setIsExporting(false);
    }
  }, [data, onExport]);

  const threatConfig = getThreatConfig(data.basicInfo.threatLevel);
  const ThreatIcon = threatConfig.icon;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* ヘッダー */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">分析レポート</h2>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-4 h-4" />
                  <span>分析日時: {format(new Date(data.analyzedAt), 'yyyy/MM/dd HH:mm')}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <User className="w-4 h-4" />
                  <span>分析者: {data.analyst.name}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleExport('json')}
              disabled={isExporting}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              title="JSONエクスポート"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={() => handleExport('csv')}
              disabled={isExporting}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              title="CSVエクスポート"
            >
              <FileText className="w-5 h-5" />
            </button>
            <button
              onClick={() => handleExport('pdf')}
              disabled={isExporting}
              className="btn-primary disabled:opacity-50"
              title="PDFエクスポート"
            >
              {isExporting ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              PDF出力
            </button>
            <button
              onClick={onShare}
              className="btn-outline"
              title="共有"
            >
              <Share2 className="w-4 h-4 mr-2" />
              共有
            </button>
          </div>
        </div>
      </div>

      {/* 概要セクション */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">概要</h3>
          <button
            onClick={() => toggleSection('summary')}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            {expandedSections.has('summary') ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expandedSections.has('summary') && (
          <div className="space-y-4">
            {/* 基本情報カード */}
            <div className={`p-4 rounded-lg border ${threatConfig.bgColor} ${threatConfig.borderColor}`}>
              <div className="flex items-center space-x-3 mb-3">
                <ThreatIcon className={`w-6 h-6 ${threatConfig.color}`} />
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">
                    {threatConfig.label} (スコア: {data.basicInfo.threatScore.toFixed(1)})
                  </h4>
                  <p className="text-sm text-gray-600">
                    類似度: {data.basicInfo.similarityScore.toFixed(1)}% •
                    ドメイン: {data.domain} •
                    ステータス: {data.basicInfo.status}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">検出詳細</h5>
                  <div className="space-y-1 text-sm text-gray-600">
                    <div>元画像: {data.basicInfo.originalImageTitle}</div>
                    <div>検出画像: {data.basicInfo.detectedImageTitle}</div>
                    <div>検出URL: {data.detectedUrl}</div>
                    <div>公式サイト: {data.basicInfo.isOfficial ? 'はい' : 'いいえ'}</div>
                  </div>
                </div>

                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">分析情報</h5>
                  <div className="space-y-1 text-sm text-gray-600">
                    <div>分析ID: {data.id}</div>
                    <div>画像ID: {data.imageId}</div>
                    <div>最終更新: {format(new Date(data.lastUpdated), 'yyyy/MM/dd HH:mm')}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* スコア内訳 */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">スコア内訳</h4>
              <div className="space-y-3">
                {Object.entries(data.scoreBreakdown).map(([key, breakdown]) => (
                  <div key={key} className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">
                          {key === 'domainTrust' ? 'ドメイン信頼度' :
                           key === 'contentSimilarity' ? 'コンテンツ類似度' :
                           key === 'aiAnalysis' ? 'AI分析' : 'コンテキスト要因'}
                        </span>
                        <span className="text-sm text-gray-600">
                          {breakdown.score.toFixed(1)} (重み: {(breakdown.weight * 100).toFixed(0)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${breakdown.score}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* AI分析結果セクション */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">AI分析結果</h3>
          <button
            onClick={() => toggleSection('aiAnalysis')}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            {expandedSections.has('aiAnalysis') ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expandedSections.has('aiAnalysis') && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(data.aiAnalysis).map(([key, analysis]) => (
              <div key={key} className="p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  {key === 'contentAbuse' ? 'コンテンツ悪用' :
                   key === 'copyrightInfringement' ? '著作権侵害' :
                   key === 'commercialUse' ? '商用利用' :
                   key === 'unauthorizedRepost' ? '無許可転載' : 'コンテンツ改変'}
                </h4>

                <div className="space-y-2">
                  {'score' in analysis && typeof analysis.score === 'number' && (
                    <div className="flex items-center justify-between text-sm">
                      <span>スコア:</span>
                      <span className={`font-medium ${analysis.score > 70 ? 'text-red-600' : 'text-green-600'}`}>
                        {analysis.score.toFixed(1)}%
                      </span>
                    </div>
                  )}

                  {'probability' in analysis && typeof analysis.probability === 'number' && (
                    <div className="flex items-center justify-between text-sm">
                      <span>確率:</span>
                      <span className={`font-medium ${analysis.probability > 70 ? 'text-red-600' : 'text-green-600'}`}>
                        {analysis.probability.toFixed(1)}%
                      </span>
                    </div>
                  )}

                  {'detected' in analysis && typeof analysis.detected === 'boolean' && (
                    <div className="flex items-center justify-between text-sm">
                      <span>検出:</span>
                      <span className={`font-medium ${analysis.detected ? 'text-red-600' : 'text-green-600'}`}>
                        {analysis.detected ? 'あり' : 'なし'}
                      </span>
                    </div>
                  )}

                  {'level' in analysis && (
                    <div className="flex items-center justify-between text-sm">
                      <span>改変レベル:</span>
                      <span className="font-medium">
                        {analysis.level === 'none' ? 'なし' :
                         analysis.level === 'slight' ? '軽微' :
                         analysis.level === 'moderate' ? '中程度' :
                         analysis.level === 'significant' ? '大幅' : analysis.level}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-sm">
                    <span>信頼度:</span>
                    <span className="font-medium">
                      {typeof analysis.confidence === 'number' ? analysis.confidence.toFixed(1) : '0.0'}%
                    </span>
                  </div>

                  {(() => {
                    // evidence または modifications プロパティをチェック
                    const evidenceList = 'evidence' in analysis ? analysis.evidence :
                                        'modifications' in analysis ? analysis.modifications : null;

                    if (evidenceList && evidenceList.length > 0) {
                      return (
                        <div className="mt-2">
                          <span className="text-xs font-medium text-gray-700">
                            {'evidence' in analysis ? '根拠:' : '改変内容:'}
                          </span>
                          <ul className="mt-1 text-xs text-gray-600 space-y-1">
                            {evidenceList.slice(0, 3).map((item, index) => (
                              <li key={index} className="flex items-start space-x-1">
                                <span>•</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      );
                    }
                    return null;
                  })()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* リスク要因セクション */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">リスク要因</h3>
          <button
            onClick={() => toggleSection('riskFactors')}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            {expandedSections.has('riskFactors') ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expandedSections.has('riskFactors') && (
          <div className="space-y-3">
            {data.riskFactors.map((risk, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border-l-4 ${
                  risk.severity === 'high' ? 'bg-red-50 border-red-400' :
                  risk.severity === 'medium' ? 'bg-yellow-50 border-yellow-400' :
                  'bg-blue-50 border-blue-400'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-gray-900">{risk.description}</h4>
                    <p className="text-xs text-gray-600 mt-1">{risk.impact}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded ${
                    risk.severity === 'high' ? 'bg-red-100 text-red-800' :
                    risk.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {risk.severity === 'high' ? '高' : risk.severity === 'medium' ? '中' : '低'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 推奨アクションセクション */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">推奨アクション</h3>
          <button
            onClick={() => toggleSection('recommendations')}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            {expandedSections.has('recommendations') ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>

        {expandedSections.has('recommendations') && (
          <div className="space-y-3">
            {data.recommendations.map((rec, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-sm font-semibold text-gray-900">{rec.action}</h4>
                  <span className={`px-2 py-1 text-xs font-medium rounded ${
                    rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                    rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {rec.priority === 'high' ? '高優先度' : rec.priority === 'medium' ? '中優先度' : '低優先度'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>期限: {rec.timeline}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 手動評価・コメントセクション */}
      {(data.manualEvaluation || data.comments.length > 0) && (
        <div className="p-6 border-t border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">手動評価・コメント</h3>
            <button
              onClick={() => toggleSection('manual')}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              {expandedSections.has('manual') ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>

          {expandedSections.has('manual') && (
            <div className="space-y-4">
              {data.manualEvaluation && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">手動評価</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <div>評価者: {data.manualEvaluation.evaluatedBy}</div>
                      <div>評価日時: {format(new Date(data.manualEvaluation.evaluatedAt), 'yyyy/MM/dd HH:mm')}</div>
                      <div>信頼度: {data.manualEvaluation.confidence}%</div>
                    </div>
                    <div>
                      {data.manualEvaluation.overrideScore && (
                        <div>修正スコア: {data.manualEvaluation.overrideScore}</div>
                      )}
                      {data.manualEvaluation.overrideThreatLevel && (
                        <div>修正脅威レベル: {data.manualEvaluation.overrideThreatLevel}</div>
                      )}
                    </div>
                  </div>
                  {data.manualEvaluation.notes && (
                    <div className="mt-2">
                      <span className="text-sm font-medium text-gray-700">備考:</span>
                      <p className="text-sm text-gray-600 mt-1">{data.manualEvaluation.notes}</p>
                    </div>
                  )}
                </div>
              )}

              {data.comments.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">コメント履歴</h4>
                  <div className="space-y-3">
                    {data.comments.map((comment) => (
                      <div key={comment.id} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-900">{comment.author}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-gray-500">
                              {format(new Date(comment.createdAt), 'yyyy/MM/dd HH:mm')}
                            </span>
                            {comment.isInternal && (
                              <span className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded">
                                内部
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600">{comment.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// CSV生成関数
const generateCSVContent = (data: AnalysisReportData): string => {
  const rows = [
    ['項目', '値'],
    ['分析ID', data.id],
    ['画像ID', data.imageId],
    ['検出URL', data.detectedUrl],
    ['ドメイン', data.domain],
    ['分析日時', data.analyzedAt],
    ['脅威レベル', data.basicInfo.threatLevel],
    ['脅威スコア', data.basicInfo.threatScore.toString()],
    ['類似度', data.basicInfo.similarityScore.toString()],
    ['ステータス', data.basicInfo.status],
    ['公式サイト', data.basicInfo.isOfficial ? 'はい' : 'いいえ'],
    [''],
    ['AI分析結果', ''],
    ['コンテンツ悪用スコア', data.aiAnalysis.contentAbuse.score.toString()],
    ['著作権侵害確率', data.aiAnalysis.copyrightInfringement.probability.toString()],
    ['商用利用検出', data.aiAnalysis.commercialUse.detected ? 'はい' : 'いいえ'],
    ['無許可転載検出', data.aiAnalysis.unauthorizedRepost.detected ? 'はい' : 'いいえ'],
    [''],
    ['リスク要因', ''],
    ...data.riskFactors.map(risk => [risk.description, risk.severity]),
  ];

  return rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
};

export default AnalysisReport;