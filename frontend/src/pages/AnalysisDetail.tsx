import React, { useState, useCallback, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  RefreshCw,
  Share2,
  Download,
  MessageCircle,
  Edit,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Calendar,
  Globe,
  Eye,
  EyeOff,
  Save,
  X,
  Plus,
  History,
  Search,
  Zap,
  FileText,
} from 'lucide-react';
import toast from 'react-hot-toast';

import ImageComparison from '../components/ImageComparison';
import AnalysisReport from '../components/AnalysisReport';
import {
  AnalysisService,
  ManualEvaluationRequest,
  CommentRequest,
  AnalysisUpdateRequest,
} from '../services/analysisService';

const AnalysisDetail: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  // 状態管理
  const [activeTab, setActiveTab] = useState<'overview' | 'comparison' | 'report' | 'history'>('overview');
  const [showManualEvaluation, setShowManualEvaluation] = useState(false);
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);

  // 手動評価フォーム
  const [manualEvaluation, setManualEvaluation] = useState<Partial<ManualEvaluationRequest>>({
    notes: '',
    confidence: 80,
  });

  // コメントフォーム
  const [newComment, setNewComment] = useState<Partial<CommentRequest>>({
    content: '',
    author: 'Current User', // 実際のアプリでは認証ユーザーから取得
    isInternal: false,
  });

  if (!analysisId) {
    return <div>分析IDが指定されていません</div>;
  }

  // データ取得
  const {
    data: analysisData,
    isLoading: isAnalysisLoading,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useQuery({
    queryKey: ['analysisDetail', analysisId],
    queryFn: () => AnalysisService.getAnalysisDetail(analysisId),
    refetchOnWindowFocus: false,
  });

  const {
    data: comparisonData,
    isLoading: isComparisonLoading,
  } = useQuery({
    queryKey: ['imageComparison', analysisId],
    queryFn: () => AnalysisService.getImageComparison(analysisId),
    refetchOnWindowFocus: false,
  });

  const {
    data: historyData,
  } = useQuery({
    queryKey: ['analysisHistory', analysisId],
    queryFn: () => AnalysisService.getAnalysisHistory(analysisId),
    enabled: activeTab === 'history',
    refetchOnWindowFocus: false,
  });

  const {
    data: similarAnalyses,
  } = useQuery({
    queryKey: ['similarAnalyses', analysisId],
    queryFn: () => AnalysisService.findSimilarAnalyses(analysisId),
    refetchOnWindowFocus: false,
  });

  // ミューテーション
  const manualEvaluationMutation = useMutation({
    mutationFn: (evaluation: ManualEvaluationRequest) =>
      AnalysisService.submitManualEvaluation(evaluation),
    onSuccess: () => {
      toast.success('手動評価を送信しました');
      setShowManualEvaluation(false);
      queryClient.invalidateQueries({ queryKey: ['analysisDetail', analysisId] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : '手動評価の送信に失敗しました');
    },
  });

  const commentMutation = useMutation({
    mutationFn: (comment: CommentRequest) =>
      AnalysisService.addComment(comment),
    onSuccess: () => {
      toast.success('コメントを追加しました');
      setShowCommentForm(false);
      setNewComment({ content: '', author: 'Current User', isInternal: false });
      queryClient.invalidateQueries({ queryKey: ['analysisDetail', analysisId] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'コメントの追加に失敗しました');
    },
  });

  const statusUpdateMutation = useMutation({
    mutationFn: (updates: AnalysisUpdateRequest) =>
      AnalysisService.updateAnalysisStatus(analysisId, updates),
    onSuccess: () => {
      toast.success('ステータスを更新しました');
      queryClient.invalidateQueries({ queryKey: ['analysisDetail', analysisId] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'ステータスの更新に失敗しました');
    },
  });

  const rerunMutation = useMutation({
    mutationFn: () => AnalysisService.rerunAnalysis(analysisId, { includeAI: true, includeSimilarity: true }),
    onSuccess: () => {
      toast.success('分析を再実行しています...');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['analysisDetail', analysisId] });
      }, 5000);
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : '分析の再実行に失敗しました');
    },
  });

  // 手動評価送信
  const handleSubmitManualEvaluation = useCallback(() => {
    if (!manualEvaluation.notes?.trim()) {
      toast.error('評価内容を入力してください');
      return;
    }

    manualEvaluationMutation.mutate({
      analysisId,
      ...manualEvaluation,
      evaluatedBy: 'Current User', // 実際のアプリでは認証ユーザーから取得
    } as ManualEvaluationRequest);
  }, [analysisId, manualEvaluation, manualEvaluationMutation]);

  // コメント送信
  const handleSubmitComment = useCallback(() => {
    if (!newComment.content?.trim()) {
      toast.error('コメント内容を入力してください');
      return;
    }

    commentMutation.mutate({
      analysisId,
      ...newComment,
    } as CommentRequest);
  }, [analysisId, newComment, commentMutation]);

  // ステータス更新
  const handleStatusUpdate = useCallback((status: 'ACTIVE' | 'REMOVED' | 'INVESTIGATING') => {
    statusUpdateMutation.mutate({ status });
  }, [statusUpdateMutation]);

  // エクスポート
  const handleExport = useCallback(async (format: 'pdf' | 'csv' | 'json') => {
    try {
      const blob = await AnalysisService.exportAnalysis(analysisId, { format });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis-${analysisId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export error:', error);
    }
  }, [analysisId]);

  // 共有
  const handleShare = useCallback(async () => {
    try {
      const { shareUrl } = await AnalysisService.generateShareLink(analysisId);
      await navigator.clipboard.writeText(shareUrl);
      toast.success('共有リンクをクリップボードにコピーしました');
      setShowShareDialog(false);
    } catch (error) {
      toast.error('共有リンクの生成に失敗しました');
    }
  }, [analysisId]);

  // 類似度領域クリック
  const handleRegionClick = useCallback((regionId: string) => {
    console.log('Region clicked:', regionId);
    // 領域の詳細表示などの処理
  }, []);

  // エラー処理
  if (analysisError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            分析データの取得に失敗しました
          </h2>
          <p className="text-gray-600 mb-4">
            {analysisError instanceof Error ? analysisError.message : 'ネットワークエラーが発生しました'}
          </p>
          <div className="flex space-x-3 justify-center">
            <button onClick={() => refetchAnalysis()} className="btn-primary">
              再試行
            </button>
            <button onClick={() => navigate(-1)} className="btn-outline">
              戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="戻る"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>

              <div>
                <h1 className="text-2xl font-bold text-gray-900">詳細分析</h1>
                <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                  <span>分析ID: {analysisId}</span>
                  {analysisData && (
                    <>
                      <span>•</span>
                      <div className="flex items-center space-x-1">
                        <Globe className="w-4 h-4" />
                        <span>{analysisData.domain}</span>
                      </div>
                      <span>•</span>
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(analysisData.analyzedAt).toLocaleDateString()}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* ステータス更新 */}
              {analysisData && (
                <select
                  value={analysisData.basicInfo.status}
                  onChange={(e) => handleStatusUpdate(e.target.value as any)}
                  className="input text-sm"
                  disabled={statusUpdateMutation.isPending}
                >
                  <option value="ACTIVE">アクティブ</option>
                  <option value="INVESTIGATING">調査中</option>
                  <option value="REMOVED">削除済み</option>
                </select>
              )}

              <button
                onClick={() => rerunMutation.mutate()}
                disabled={rerunMutation.isPending || isAnalysisLoading}
                className="p-2 text-gray-400 hover:text-blue-600 transition-colors disabled:opacity-50"
                title="分析を再実行"
              >
                <RefreshCw className={`w-5 h-5 ${rerunMutation.isPending ? 'animate-spin' : ''}`} />
              </button>

              <button
                onClick={() => setShowShareDialog(true)}
                className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                title="共有"
              >
                <Share2 className="w-5 h-5" />
              </button>

              <button
                onClick={() => handleExport('pdf')}
                className="btn-primary"
                title="PDFエクスポート"
              >
                <Download className="w-4 h-4 mr-2" />
                エクスポート
              </button>
            </div>
          </div>

          {/* タブナビゲーション */}
          <div className="mt-6">
            <nav className="flex space-x-8">
              {[
                { id: 'overview', label: '概要', icon: Eye },
                { id: 'comparison', label: '画像比較', icon: Search },
                { id: 'report', label: 'レポート', icon: FileText },
                { id: 'history', label: '履歴', icon: History },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id as any)}
                  className={`flex items-center space-x-2 pb-4 border-b-2 transition-colors ${
                    activeTab === id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isAnalysisLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">分析データを読み込み中...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* メインコンテンツ */}
            <div className="lg:col-span-3">
              {activeTab === 'overview' && analysisData && (
                <div className="space-y-6">
                  {/* 基本情報カード */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-semibold text-gray-900">基本情報</h2>
                      <div className="flex items-center space-x-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          analysisData.basicInfo.threatLevel === 'HIGH' ? 'bg-red-100 text-red-800' :
                          analysisData.basicInfo.threatLevel === 'MEDIUM' ? 'bg-orange-100 text-orange-800' :
                          analysisData.basicInfo.threatLevel === 'LOW' ? 'bg-yellow-100 text-yellow-800' :
                          analysisData.basicInfo.threatLevel === 'SAFE' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {analysisData.basicInfo.threatLevel === 'HIGH' ? '高リスク' :
                           analysisData.basicInfo.threatLevel === 'MEDIUM' ? '中リスク' :
                           analysisData.basicInfo.threatLevel === 'LOW' ? '低リスク' :
                           analysisData.basicInfo.threatLevel === 'SAFE' ? '安全' : '不明'}
                        </span>
                        <span className="text-sm text-gray-600">
                          スコア: {analysisData.basicInfo.threatScore.toFixed(1)}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-3">検出情報</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">元画像:</span>
                            <span className="font-medium">{analysisData.basicInfo.originalImageTitle}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">検出画像:</span>
                            <span className="font-medium">{analysisData.basicInfo.detectedImageTitle}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">類似度:</span>
                            <span className="font-medium">{analysisData.basicInfo.similarityScore.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">公式サイト:</span>
                            <span className="font-medium">
                              {analysisData.basicInfo.isOfficial ? 'はい' : 'いいえ'}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-3">分析情報</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">分析者:</span>
                            <span className="font-medium">{analysisData.analyst.name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">分析日時:</span>
                            <span className="font-medium">
                              {new Date(analysisData.analyzedAt).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">最終更新:</span>
                            <span className="font-medium">
                              {new Date(analysisData.lastUpdated).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">ステータス:</span>
                            <span className="font-medium">
                              {analysisData.basicInfo.status === 'ACTIVE' ? 'アクティブ' :
                               analysisData.basicInfo.status === 'INVESTIGATING' ? '調査中' : '削除済み'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* AI分析結果概要 */}
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">AI分析結果</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">コンテンツ悪用</span>
                          <span className={`text-sm font-medium ${
                            analysisData.aiAnalysis.contentAbuse.score > 70 ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {analysisData.aiAnalysis.contentAbuse.score.toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">著作権侵害</span>
                          <span className={`text-sm font-medium ${
                            analysisData.aiAnalysis.copyrightInfringement.probability > 70 ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {analysisData.aiAnalysis.copyrightInfringement.probability.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">商用利用</span>
                          <span className={`text-sm font-medium ${
                            analysisData.aiAnalysis.commercialUse.detected ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {analysisData.aiAnalysis.commercialUse.detected ? 'あり' : 'なし'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">無許可転載</span>
                          <span className={`text-sm font-medium ${
                            analysisData.aiAnalysis.unauthorizedRepost.detected ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {analysisData.aiAnalysis.unauthorizedRepost.detected ? 'あり' : 'なし'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'comparison' && comparisonData && (
                <div className="space-y-6">
                  <ImageComparison
                    originalImage={comparisonData.originalImage}
                    detectedImage={comparisonData.detectedImage}
                    similarityData={comparisonData.similarityData}
                    onRegionClick={handleRegionClick}
                  />
                </div>
              )}

              {activeTab === 'report' && analysisData && (
                <div className="space-y-6">
                  <AnalysisReport
                    data={analysisData}
                    onExport={handleExport}
                    onShare={() => setShowShareDialog(true)}
                  />
                </div>
              )}

              {activeTab === 'history' && historyData && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                  <div className="p-6 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-900">分析履歴</h2>
                  </div>
                  <div className="divide-y divide-gray-200">
                    {historyData.map((entry) => (
                      <div key={entry.id} className="p-6">
                        <div className="flex items-start space-x-4">
                          <div className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h3 className="text-sm font-medium text-gray-900">{entry.action}</h3>
                              <span className="text-xs text-gray-500">
                                {new Date(entry.performedAt).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{entry.details}</p>
                            <div className="flex items-center space-x-2 mt-2">
                              <User className="w-3 h-3 text-gray-400" />
                              <span className="text-xs text-gray-500">{entry.performedBy}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* サイドバー */}
            <div className="lg:col-span-1 space-y-6">
              {/* アクションパネル */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">アクション</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => setShowManualEvaluation(!showManualEvaluation)}
                    className="w-full btn-outline text-sm"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    手動評価
                  </button>
                  <button
                    onClick={() => setShowCommentForm(!showCommentForm)}
                    className="w-full btn-outline text-sm"
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    コメント追加
                  </button>
                  <button
                    onClick={() => rerunMutation.mutate()}
                    disabled={rerunMutation.isPending}
                    className="w-full btn-outline text-sm disabled:opacity-50"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    分析再実行
                  </button>
                </div>
              </div>

              {/* 手動評価フォーム */}
              {showManualEvaluation && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-900">手動評価</h3>
                    <button
                      onClick={() => setShowManualEvaluation(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="label">脅威レベル修正</label>
                      <select
                        value={manualEvaluation.overrideThreatLevel || ''}
                        onChange={(e) => setManualEvaluation(prev => ({
                          ...prev,
                          overrideThreatLevel: e.target.value as any || undefined
                        }))}
                        className="input text-sm"
                      >
                        <option value="">選択してください</option>
                        <option value="SAFE">安全</option>
                        <option value="LOW">低リスク</option>
                        <option value="MEDIUM">中リスク</option>
                        <option value="HIGH">高リスク</option>
                      </select>
                    </div>

                    <div>
                      <label className="label">スコア修正</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={manualEvaluation.overrideScore || ''}
                        onChange={(e) => setManualEvaluation(prev => ({
                          ...prev,
                          overrideScore: e.target.value ? parseFloat(e.target.value) : undefined
                        }))}
                        className="input text-sm"
                        placeholder="0-100"
                      />
                    </div>

                    <div>
                      <label className="label">信頼度 (%)</label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={manualEvaluation.confidence || 80}
                        onChange={(e) => setManualEvaluation(prev => ({
                          ...prev,
                          confidence: parseInt(e.target.value)
                        }))}
                        className="w-full"
                      />
                      <div className="text-xs text-gray-500 text-center mt-1">
                        {manualEvaluation.confidence || 80}%
                      </div>
                    </div>

                    <div>
                      <label className="label">評価内容</label>
                      <textarea
                        value={manualEvaluation.notes || ''}
                        onChange={(e) => setManualEvaluation(prev => ({
                          ...prev,
                          notes: e.target.value
                        }))}
                        className="input text-sm"
                        rows={4}
                        placeholder="評価内容と根拠を記載してください..."
                      />
                    </div>

                    <button
                      onClick={handleSubmitManualEvaluation}
                      disabled={manualEvaluationMutation.isPending}
                      className="w-full btn-primary text-sm disabled:opacity-50"
                    >
                      {manualEvaluationMutation.isPending ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          送信中...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4 mr-2" />
                          評価を送信
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* コメントフォーム */}
              {showCommentForm && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-900">コメント追加</h3>
                    <button
                      onClick={() => setShowCommentForm(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={newComment.isInternal || false}
                          onChange={(e) => setNewComment(prev => ({
                            ...prev,
                            isInternal: e.target.checked
                          }))}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">内部コメント</span>
                      </label>
                    </div>

                    <div>
                      <label className="label">コメント内容</label>
                      <textarea
                        value={newComment.content || ''}
                        onChange={(e) => setNewComment(prev => ({
                          ...prev,
                          content: e.target.value
                        }))}
                        className="input text-sm"
                        rows={4}
                        placeholder="コメントを入力してください..."
                      />
                    </div>

                    <button
                      onClick={handleSubmitComment}
                      disabled={commentMutation.isPending}
                      className="w-full btn-primary text-sm disabled:opacity-50"
                    >
                      {commentMutation.isPending ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          送信中...
                        </>
                      ) : (
                        <>
                          <Plus className="w-4 h-4 mr-2" />
                          コメント追加
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* 類似分析 */}
              {similarAnalyses && similarAnalyses.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">類似分析</h3>
                  <div className="space-y-3">
                    {similarAnalyses.slice(0, 5).map((similar) => (
                      <div
                        key={similar.id}
                        className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                        onClick={() => navigate(`/analysis/${similar.id}`)}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-gray-900 truncate">
                            {similar.domain}
                          </span>
                          <span className="text-xs text-gray-500">
                            {similar.similarityScore.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <span>スコア: {similar.threatScore.toFixed(1)}</span>
                          <span>{new Date(similar.analyzedAt).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 共有ダイアログ */}
      {showShareDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">分析結果を共有</h3>
              <button
                onClick={() => setShowShareDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              この分析結果の共有リンクを生成します。リンクを知っている人は誰でもアクセスできます。
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleShare}
                className="btn-primary flex-1"
              >
                <Share2 className="w-4 h-4 mr-2" />
                共有リンク生成
              </button>
              <button
                onClick={() => setShowShareDialog(false)}
                className="btn-outline flex-1"
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisDetail;