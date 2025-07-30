import { useQuery } from '@tanstack/react-query';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { api } from '../services/api';

// TypeScript型定義
export interface DashboardStats {
  todayScans: number;
  threatDetections: number;
  processingTasks: number;
  totalImages: number;
  trends: {
    scansChange: number;
    threatsChange: number;
    tasksChange: number;
  };
}

export interface ThreatDistribution {
  SAFE: number;
  LOW: number;
  MEDIUM: number;
  HIGH: number;
  UNKNOWN: number;
}

export interface DailyDetection {
  date: string;
  totalScans: number;
  threatDetections: number;
  safeDetections: number;
  lowRisk: number;
  mediumRisk: number;
  highRisk: number;
}

export interface RecentDetection {
  id: string;
  imageId: string;
  url: string;
  domain: string;
  threatLevel: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  threatScore: number;
  detectedAt: string;
  riskFactors: string[];
  status: 'PROCESSING' | 'COMPLETED' | 'FAILED';
}

export interface DashboardData {
  stats: DashboardStats;
  threatDistribution: ThreatDistribution;
  dailyDetections: DailyDetection[];
  recentDetections: RecentDetection[];
}

// ダッシュボード統計データを取得
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async (): Promise<DashboardStats> => {
      try {
        // 複数のエンドポイントからデータを取得
        const [statsResponse, imagesResponse] = await Promise.all([
          api.get('/api/v1/threat-scoring/statistics'),
          api.get('/api/v1/images?limit=1') // 画像総数を取得するため
        ]);

        const threatStats = statsResponse.data;
        const today = format(new Date(), 'yyyy-MM-dd');

        // 今日のデータをフィルタリング（模擬データ）
        const todayScans = Math.floor(Math.random() * 100) + 50;
        const threatDetections = Math.floor(todayScans * 0.15); // 15%が脅威検出
        const processingTasks = Math.floor(Math.random() * 10) + 2;

        // 前日比の計算（模擬データ）
        const scansChange = Math.floor(Math.random() * 40) - 20; // -20 ~ +20%
        const threatsChange = Math.floor(Math.random() * 60) - 30; // -30 ~ +30%
        const tasksChange = Math.floor(Math.random() * 20) - 10; // -10 ~ +10%

        return {
          todayScans,
          threatDetections,
          processingTasks,
          totalImages: threatStats.total_assessments || 0,
          trends: {
            scansChange,
            threatsChange,
            tasksChange,
          },
        };
      } catch (error) {
        console.error('Dashboard stats fetch error:', error);
        // フォールバック用のデフォルトデータ
        return {
          todayScans: 0,
          threatDetections: 0,
          processingTasks: 0,
          totalImages: 0,
          trends: {
            scansChange: 0,
            threatsChange: 0,
            tasksChange: 0,
          },
        };
      }
    },
    refetchInterval: 30000, // 30秒ごとに更新
    staleTime: 15000, // 15秒間はキャッシュを使用
  });
};

// 脅威レベル分布データを取得
export const useThreatDistribution = () => {
  return useQuery({
    queryKey: ['dashboard', 'threat-distribution'],
    queryFn: async (): Promise<ThreatDistribution> => {
      try {
        const response = await api.get('/api/v1/threat-scoring/statistics');
        const stats = response.data;

        return {
          SAFE: stats.score_distribution?.SAFE || 0,
          LOW: stats.score_distribution?.LOW || 0,
          MEDIUM: stats.score_distribution?.MEDIUM || 0,
          HIGH: stats.score_distribution?.HIGH || 0,
          UNKNOWN: stats.score_distribution?.UNKNOWN || 0,
        };
      } catch (error) {
        console.error('Threat distribution fetch error:', error);
        // フォールバック用のデフォルトデータ
        return {
          SAFE: 45,
          LOW: 25,
          MEDIUM: 20,
          HIGH: 8,
          UNKNOWN: 2,
        };
      }
    },
    refetchInterval: 60000, // 1分ごとに更新
    staleTime: 30000, // 30秒間はキャッシュを使用
  });
};

// 日別検出数推移データを取得
export const useDailyDetections = (days: number = 7) => {
  return useQuery({
    queryKey: ['dashboard', 'daily-detections', days],
    queryFn: async (): Promise<DailyDetection[]> => {
      try {
        // 実際のAPIが実装されるまでは模擬データを生成
        const dailyData: DailyDetection[] = [];

        for (let i = days - 1; i >= 0; i--) {
          const date = format(subDays(new Date(), i), 'yyyy-MM-dd');
          const totalScans = Math.floor(Math.random() * 80) + 40;
          const threatDetections = Math.floor(totalScans * (0.1 + Math.random() * 0.2));
          const safeDetections = totalScans - threatDetections;

          // 脅威レベル別の分布
          const highRisk = Math.floor(threatDetections * 0.1);
          const mediumRisk = Math.floor(threatDetections * 0.3);
          const lowRisk = threatDetections - highRisk - mediumRisk;

          dailyData.push({
            date,
            totalScans,
            threatDetections,
            safeDetections,
            lowRisk,
            mediumRisk,
            highRisk,
          });
        }

        return dailyData;
      } catch (error) {
        console.error('Daily detections fetch error:', error);
        return [];
      }
    },
    refetchInterval: 300000, // 5分ごとに更新
    staleTime: 120000, // 2分間はキャッシュを使用
  });
};

// 最近の検出一覧を取得
export const useRecentDetections = (limit: number = 10) => {
  return useQuery({
    queryKey: ['dashboard', 'recent-detections', limit],
    queryFn: async (): Promise<RecentDetection[]> => {
      try {
        // 実際のAPIが実装されるまでは模擬データを生成
        const mockDetections: RecentDetection[] = [];
        const domains = ['example.com', 'test-site.org', 'sample.net', 'demo.co.jp', 'mock-site.com'];
        const threatLevels: Array<'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN'> = ['SAFE', 'LOW', 'MEDIUM', 'HIGH', 'UNKNOWN'];
        const riskFactorsPool = [
          '新規ドメイン（30日以内）',
          'SSL証明書なし',
          '著作権侵害の可能性',
          '検索順位が低い',
          'コンテンツ類似度が低い',
          '高い悪用リスク',
          '無許可商用利用',
        ];

        for (let i = 0; i < limit; i++) {
          const threatLevel = threatLevels[Math.floor(Math.random() * threatLevels.length)];
          const domain = domains[Math.floor(Math.random() * domains.length)];
          const riskFactorCount = Math.floor(Math.random() * 3) + 1;
          const riskFactors = riskFactorsPool
            .sort(() => 0.5 - Math.random())
            .slice(0, riskFactorCount);

          mockDetections.push({
            id: `detection-${i + 1}`,
            imageId: `img-${Math.floor(Math.random() * 10000)}`,
            url: `https://${domain}/page${i + 1}`,
            domain,
            threatLevel,
            threatScore: threatLevel === 'HIGH' ? 85 + Math.random() * 15 :
                         threatLevel === 'MEDIUM' ? 60 + Math.random() * 20 :
                         threatLevel === 'LOW' ? 40 + Math.random() * 20 :
                         Math.random() * 40,
            detectedAt: format(subDays(new Date(), Math.floor(Math.random() * 7)), 'yyyy-MM-dd\'T\'HH:mm:ss\'Z\''),
            riskFactors,
            status: i < 2 ? 'PROCESSING' : 'COMPLETED',
          });
        }

        return mockDetections.sort((a, b) =>
          new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime()
        );
      } catch (error) {
        console.error('Recent detections fetch error:', error);
        return [];
      }
    },
    refetchInterval: 15000, // 15秒ごとに更新
    staleTime: 10000, // 10秒間はキャッシュを使用
  });
};

// 全てのダッシュボードデータを統合して取得するカスタムフック
export const useDashboardData = () => {
  const statsQuery = useDashboardStats();
  const distributionQuery = useThreatDistribution();
  const dailyQuery = useDailyDetections();
  const recentQuery = useRecentDetections();

  return {
    // データ
    stats: statsQuery.data,
    threatDistribution: distributionQuery.data,
    dailyDetections: dailyQuery.data,
    recentDetections: recentQuery.data,

    // ローディング状態
    isLoading: statsQuery.isLoading || distributionQuery.isLoading ||
               dailyQuery.isLoading || recentQuery.isLoading,

    // エラー状態
    isError: statsQuery.isError || distributionQuery.isError ||
             dailyQuery.isError || recentQuery.isError,

    // エラー情報
    error: statsQuery.error || distributionQuery.error ||
           dailyQuery.error || recentQuery.error,

    // リフェッチ関数
    refetch: () => {
      statsQuery.refetch();
      distributionQuery.refetch();
      dailyQuery.refetch();
      recentQuery.refetch();
    },

    // 個別のクエリ状態
    queries: {
      stats: statsQuery,
      distribution: distributionQuery,
      daily: dailyQuery,
      recent: recentQuery,
    },
  };
};

export default useDashboardData;