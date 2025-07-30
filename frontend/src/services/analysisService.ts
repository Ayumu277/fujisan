import { api } from './api';
import { AnalysisReportData } from '../components/AnalysisReport';
import { ComparisonImage, SimilarityData } from '../components/ImageComparison';

// 詳細分析リクエストの型定義
export interface AnalysisDetailRequest {
  imageId: string;
  detectedUrl?: string;
  includeAI?: boolean;
  includeSimilarity?: boolean;
  includeMetadata?: boolean;
}

// 手動評価リクエストの型定義
export interface ManualEvaluationRequest {
  analysisId: string;
  overrideScore?: number;
  overrideThreatLevel?: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  notes: string;
  confidence: number;
  evaluatedBy: string;
}

// コメント追加リクエストの型定義
export interface CommentRequest {
  analysisId: string;
  content: string;
  author: string;
  isInternal?: boolean;
}

// 分析更新リクエストの型定義
export interface AnalysisUpdateRequest {
  status?: 'ACTIVE' | 'REMOVED' | 'INVESTIGATING';
  threatLevel?: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  threatScore?: number;
  notes?: string;
}

// 分析エクスポートオプション
export interface ExportOptions {
  format: 'pdf' | 'csv' | 'json';
  includeImages?: boolean;
  includeComments?: boolean;
  includeHistory?: boolean;
}

// 詳細分析データを取得
export const getAnalysisDetail = async (analysisId: string): Promise<AnalysisReportData> => {
  try {
    const response = await api.get<AnalysisReportData>(`/api/v1/analysis/${analysisId}`);
    return response;
  } catch (error) {
    console.error('Get analysis detail error:', error);

    // フォールバック用のモックデータ
    return generateMockAnalysisData(analysisId);
  }
};

// 画像比較データを取得
export const getImageComparison = async (analysisId: string): Promise<{
  originalImage: ComparisonImage;
  detectedImage: ComparisonImage;
  similarityData: SimilarityData;
}> => {
  try {
    const response = await api.get(`/api/v1/analysis/${analysisId}/comparison`);
    return response;
  } catch (error) {
    console.error('Get image comparison error:', error);

    // フォールバック用のモックデータ
    return generateMockComparisonData(analysisId);
  }
};

// 手動評価を追加/更新
export const submitManualEvaluation = async (evaluation: ManualEvaluationRequest): Promise<void> => {
  try {
    await api.post(`/api/v1/analysis/${evaluation.analysisId}/evaluation`, evaluation);
  } catch (error) {
    console.error('Submit manual evaluation error:', error);
    throw new Error('手動評価の送信に失敗しました');
  }
};

// コメントを追加
export const addComment = async (comment: CommentRequest): Promise<void> => {
  try {
    await api.post(`/api/v1/analysis/${comment.analysisId}/comments`, comment);
  } catch (error) {
    console.error('Add comment error:', error);
    throw new Error('コメントの追加に失敗しました');
  }
};

// 分析ステータスを更新
export const updateAnalysisStatus = async (
  analysisId: string,
  updates: AnalysisUpdateRequest
): Promise<void> => {
  try {
    await api.put(`/api/v1/analysis/${analysisId}`, updates);
  } catch (error) {
    console.error('Update analysis status error:', error);
    throw new Error('分析ステータスの更新に失敗しました');
  }
};

// 分析を再実行
export const rerunAnalysis = async (
  analysisId: string,
  options?: { includeAI?: boolean; includeSimilarity?: boolean }
): Promise<{ jobId: string }> => {
  try {
    const response = await api.post(`/api/v1/analysis/${analysisId}/rerun`, options);
    return response;
  } catch (error) {
    console.error('Rerun analysis error:', error);
    throw new Error('分析の再実行に失敗しました');
  }
};

// 分析データをエクスポート
export const exportAnalysis = async (
  analysisId: string,
  options: ExportOptions
): Promise<Blob> => {
  try {
    const response = await api.get(`/api/v1/analysis/${analysisId}/export`, {
      params: options,
      responseType: 'blob',
    });
    return response as unknown as Blob;
  } catch (error) {
    console.error('Export analysis error:', error);
    throw new Error('分析データのエクスポートに失敗しました');
  }
};

// 分析履歴を取得
export const getAnalysisHistory = async (
  analysisId: string,
  limit: number = 50
): Promise<Array<{
  id: string;
  action: string;
  details: string;
  performedBy: string;
  performedAt: string;
  changes?: Record<string, any>;
}>> => {
  try {
    const response = await api.get(`/api/v1/analysis/${analysisId}/history?limit=${limit}`);
    return response.history || [];
  } catch (error) {
    console.error('Get analysis history error:', error);
    return [];
  }
};

// 類似分析を検索
export const findSimilarAnalyses = async (
  analysisId: string,
  limit: number = 10
): Promise<Array<{
  id: string;
  imageId: string;
  domain: string;
  similarityScore: number;
  threatLevel: string;
  threatScore: number;
  analyzedAt: string;
}>> => {
  try {
    const response = await api.get(`/api/v1/analysis/${analysisId}/similar?limit=${limit}`);
    return response.analyses || [];
  } catch (error) {
    console.error('Find similar analyses error:', error);
    return [];
  }
};

// 分析の共有リンクを生成
export const generateShareLink = async (
  analysisId: string,
  options?: { expiresAt?: string; password?: string; permissions?: string[] }
): Promise<{ shareUrl: string; expiresAt?: string }> => {
  try {
    const response = await api.post(`/api/v1/analysis/${analysisId}/share`, options);
    return response;
  } catch (error) {
    console.error('Generate share link error:', error);
    throw new Error('共有リンクの生成に失敗しました');
  }
};

// 分析通知設定を更新
export const updateNotificationSettings = async (
  analysisId: string,
  settings: {
    emailNotifications?: boolean;
    statusUpdates?: boolean;
    commentNotifications?: boolean;
    reminderFrequency?: 'never' | 'daily' | 'weekly';
  }
): Promise<void> => {
  try {
    await api.put(`/api/v1/analysis/${analysisId}/notifications`, settings);
  } catch (error) {
    console.error('Update notification settings error:', error);
    throw new Error('通知設定の更新に失敗しました');
  }
};

// モックデータ生成関数
const generateMockAnalysisData = (analysisId: string): AnalysisReportData => {
  const mockData: AnalysisReportData = {
    id: analysisId,
    imageId: `img-${Math.floor(Math.random() * 10000)}`,
    detectedUrl: `https://example-${Math.floor(Math.random() * 1000)}.com/image.jpg`,
    domain: `example-${Math.floor(Math.random() * 1000)}.com`,
    analyzedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    lastUpdated: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
    analyst: {
      id: 'analyst-1',
      name: '分析者 太郎',
      email: 'analyst@example.com',
    },

    basicInfo: {
      originalImageTitle: 'オリジナル画像.jpg',
      detectedImageTitle: '検出された画像.jpg',
      similarityScore: 75 + Math.random() * 20,
      threatLevel: (['SAFE', 'LOW', 'MEDIUM', 'HIGH', 'UNKNOWN'] as const)[Math.floor(Math.random() * 5)],
      threatScore: Math.random() * 100,
      status: (['ACTIVE', 'REMOVED', 'INVESTIGATING'] as const)[Math.floor(Math.random() * 3)],
      isOfficial: Math.random() < 0.2,
    },

    aiAnalysis: {
      contentAbuse: {
        score: Math.random() * 100,
        confidence: 70 + Math.random() * 30,
        evidence: ['疑わしいメタデータ改変', '類似画像の大量投稿', 'ウォーターマーク除去の痕跡'],
        details: 'AI分析により、コンテンツ悪用の可能性が検出されました。',
      },
      copyrightInfringement: {
        probability: Math.random() * 100,
        confidence: 60 + Math.random() * 40,
        evidence: ['著作権表示の削除', '商用利用の兆候', '元作品との高い類似度'],
        details: '著作権侵害の可能性が高いと判定されました。',
      },
      commercialUse: {
        detected: Math.random() < 0.4,
        confidence: 50 + Math.random() * 50,
        evidence: ['販売サイトでの使用', '広告コンテンツでの利用', '商用ライセンス情報の欠如'],
        details: '商用利用の兆候が検出されました。',
      },
      unauthorizedRepost: {
        detected: Math.random() < 0.6,
        confidence: 60 + Math.random() * 40,
        evidence: ['元投稿者と異なるアカウント', '投稿日時の矛盾', '出典情報の欠如'],
        details: '無許可転載の可能性があります。',
      },
      contentModification: {
        level: ['none', 'slight', 'moderate', 'significant'][Math.floor(Math.random() * 4)],
        confidence: 70 + Math.random() * 30,
        modifications: ['リサイズ', '色調補正', 'ウォーターマーク除去', 'トリミング'],
        details: '画像に対して改変処理が施されています。',
      },
    },

    scoreBreakdown: {
      domainTrust: {
        score: Math.random() * 100,
        weight: 0.4,
        factors: ['ドメイン年数', 'SSL証明書', 'DNS設定', 'レピュテーション'],
      },
      contentSimilarity: {
        score: Math.random() * 100,
        weight: 0.3,
        factors: ['画像ハッシュ比較', '特徴量解析', 'メタデータ比較'],
      },
      aiAnalysis: {
        score: Math.random() * 100,
        weight: 0.2,
        factors: ['コンテンツ分析', '著作権判定', '悪用検知'],
      },
      contextualFactors: {
        score: Math.random() * 100,
        weight: 0.1,
        factors: ['投稿日時', 'ソーシャルシグナル', '関連コンテンツ'],
      },
    },

    riskFactors: [
      {
        category: 'technical',
        severity: 'high' as const,
        description: 'メタデータが完全に削除されている',
        impact: '元画像の追跡が困難になる可能性',
      },
      {
        category: 'legal',
        severity: 'medium' as const,
        description: '著作権表示が除去されている',
        impact: '法的問題に発展する可能性',
      },
      {
        category: 'business',
        severity: 'low' as const,
        description: '商用サイトでの使用が確認された',
        impact: 'ブランドイメージへの影響',
      },
    ],

    recommendations: [
      {
        priority: 'high' as const,
        action: '権利者への通知',
        description: '画像の権利者に不正使用について通知することを推奨します。',
        timeline: '24時間以内',
      },
      {
        priority: 'medium' as const,
        action: 'DMCA申請',
        description: 'プラットフォームにDMCA削除申請を提出してください。',
        timeline: '3日以内',
      },
      {
        priority: 'low' as const,
        action: '継続監視',
        description: '同様の不正使用がないか継続的に監視してください。',
        timeline: '1週間以内',
      },
    ],

    manualEvaluation: Math.random() < 0.5 ? {
      evaluatedBy: '評価者 花子',
      evaluatedAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      overrideScore: 85,
      overrideThreatLevel: 'HIGH',
      notes: '手動確認の結果、高リスクと判定しました。早急な対応が必要です。',
      confidence: 95,
    } : undefined,

    comments: [
      {
        id: 'comment-1',
        author: '分析者 太郎',
        content: '初期分析を完了しました。追加調査が必要な項目があります。',
        createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        isInternal: true,
      },
      {
        id: 'comment-2',
        author: '管理者',
        content: '権利者に連絡を取りました。対応状況を更新してください。',
        createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        isInternal: false,
      },
    ],
  };

  return mockData;
};

const generateMockComparisonData = (analysisId: string) => {
  return {
    originalImage: {
      id: 'orig-1',
      url: `https://picsum.photos/800/600?random=${analysisId}`,
      title: 'オリジナル画像.jpg',
      metadata: {
        width: 800,
        height: 600,
        size: 245760,
        format: 'JPEG',
        uploadedAt: new Date().toISOString(),
      },
    },
    detectedImage: {
      id: 'det-1',
      url: `https://picsum.photos/800/600?random=${analysisId}&grayscale`,
      title: '検出された画像.jpg',
      metadata: {
        width: 800,
        height: 600,
        size: 198432,
        format: 'JPEG',
        uploadedAt: new Date().toISOString(),
      },
    },
    similarityData: {
      score: 85.7,
      regions: [
        {
          id: 'region-1',
          x: 10,
          y: 15,
          width: 30,
          height: 25,
          confidence: 92.5,
          type: 'match' as const,
        },
        {
          id: 'region-2',
          x: 50,
          y: 30,
          width: 20,
          height: 15,
          confidence: 78.3,
          type: 'modification' as const,
        },
        {
          id: 'region-3',
          x: 70,
          y: 10,
          width: 25,
          height: 20,
          confidence: 89.1,
          type: 'match' as const,
        },
      ],
    },
  };
};

export const AnalysisService = {
  getAnalysisDetail,
  getImageComparison,
  submitManualEvaluation,
  addComment,
  updateAnalysisStatus,
  rerunAnalysis,
  exportAnalysis,
  getAnalysisHistory,
  findSimilarAnalyses,
  generateShareLink,
  updateNotificationSettings,
};