import { api } from './api';
import { SearchResult } from '../components/ResultCard';
import { FilterConfig } from '../components/FilterPanel';

// 検索パラメータの型定義
export interface SearchParams {
  imageId?: string;
  query?: string;
  filters: FilterConfig;
  page: number;
  limit: number;
}

// 検索結果レスポンスの型定義
export interface SearchResultsResponse {
  results: SearchResult[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  totalPages: number;
  facets: {
    domains: Array<{ domain: string; count: number }>;
    threatLevels: Array<{ level: string; count: number }>;
    statuses: Array<{ status: string; count: number }>;
  };
}

// 検索統計の型定義
export interface SearchStats {
  totalResults: number;
  averageThreatScore: number;
  highRiskCount: number;
  activeMonitoring: number;
  lastUpdated: string;
}

// 検索結果を取得
export const searchImages = async (params: SearchParams): Promise<SearchResultsResponse> => {
  try {
    // クエリパラメータを構築
    const searchParams = new URLSearchParams();
    
    if (params.imageId) {
      searchParams.append('imageId', params.imageId);
    }
    
    if (params.query) {
      searchParams.append('query', params.query);
    }

    // ページネーション
    searchParams.append('page', params.page.toString());
    searchParams.append('limit', params.limit.toString());

    // ソート設定
    searchParams.append('sortBy', params.filters.sortBy);
    searchParams.append('sortOrder', params.filters.sortOrder);

    // フィルター設定
    if (params.filters.threatLevels.length > 0) {
      params.filters.threatLevels.forEach(level => {
        searchParams.append('threatLevels', level);
      });
    }

    if (params.filters.domains.length > 0) {
      params.filters.domains.forEach(domain => {
        searchParams.append('domains', domain);
      });
    }

    if (params.filters.status.length > 0) {
      params.filters.status.forEach(status => {
        searchParams.append('status', status);
      });
    }

    if (params.filters.dateRange.startDate) {
      searchParams.append('startDate', params.filters.dateRange.startDate);
    }

    if (params.filters.dateRange.endDate) {
      searchParams.append('endDate', params.filters.dateRange.endDate);
    }

    if (params.filters.similarityRange.min > 0) {
      searchParams.append('minSimilarity', params.filters.similarityRange.min.toString());
    }

    if (params.filters.similarityRange.max < 100) {
      searchParams.append('maxSimilarity', params.filters.similarityRange.max.toString());
    }

    if (params.filters.isOfficial !== null) {
      searchParams.append('isOfficial', params.filters.isOfficial.toString());
    }

    if (params.filters.hasRiskFactors !== null) {
      searchParams.append('hasRiskFactors', params.filters.hasRiskFactors.toString());
    }

    const response = await api.get<SearchResultsResponse>(
      `/api/v1/search/results?${searchParams.toString()}`
    );

    return response;
  } catch (error) {
    console.error('Search images error:', error);
    
    // フォールバック用のモックデータを生成
    return generateMockSearchResults(params);
  }
};

// 検索統計を取得
export const getSearchStats = async (imageId?: string): Promise<SearchStats> => {
  try {
    const url = imageId 
      ? `/api/v1/search/stats/${imageId}`
      : '/api/v1/search/stats';
    
    const response = await api.get<SearchStats>(url);
    return response;
  } catch (error) {
    console.error('Get search stats error:', error);
    
    // フォールバック用のモックデータ
    return {
      totalResults: Math.floor(Math.random() * 500) + 50,
      averageThreatScore: Math.random() * 60 + 20,
      highRiskCount: Math.floor(Math.random() * 50) + 5,
      activeMonitoring: Math.floor(Math.random() * 20) + 3,
      lastUpdated: new Date().toISOString(),
    };
  }
};

// 利用可能なドメインを取得
export const getAvailableDomains = async (): Promise<string[]> => {
  try {
    const response = await api.get<{ domains: string[] }>('/api/v1/search/domains');
    return response.domains;
  } catch (error) {
    console.error('Get available domains error:', error);
    
    // フォールバック用のモックドメイン
    return [
      'example.com',
      'test-site.org',
      'sample.net',
      'demo.co.jp',
      'mock-site.com',
      'photo-sharing.io',
      'art-gallery.net',
      'social-media.com',
      'blog-platform.org',
      'news-site.jp',
      'e-commerce.store',
      'portfolio.dev',
      'creative-works.art',
      'image-host.cloud',
      'content-site.info',
    ];
  }
};

// 特定の検索結果の詳細を取得
export const getSearchResultDetails = async (resultId: string): Promise<SearchResult> => {
  try {
    const response = await api.get<SearchResult>(`/api/v1/search/results/${resultId}`);
    return response;
  } catch (error) {
    console.error('Get search result details error:', error);
    throw new Error('検索結果の詳細取得に失敗しました');
  }
};

// 検索結果のステータスを更新
export const updateSearchResultStatus = async (
  resultId: string, 
  status: 'ACTIVE' | 'REMOVED' | 'INVESTIGATING'
): Promise<void> => {
  try {
    await api.put(`/api/v1/search/results/${resultId}/status`, { status });
  } catch (error) {
    console.error('Update search result status error:', error);
    throw new Error('ステータスの更新に失敗しました');
  }
};

// 検索結果を削除
export const deleteSearchResult = async (resultId: string): Promise<void> => {
  try {
    await api.delete(`/api/v1/search/results/${resultId}`);
  } catch (error) {
    console.error('Delete search result error:', error);
    throw new Error('検索結果の削除に失敗しました');
  }
};

// モックデータ生成関数
const generateMockSearchResults = (params: SearchParams): SearchResultsResponse => {
  const mockDomains = [
    'example.com', 'test-site.org', 'sample.net', 'demo.co.jp', 'mock-site.com',
    'photo-sharing.io', 'art-gallery.net', 'social-media.com', 'blog-platform.org',
    'news-site.jp', 'e-commerce.store', 'portfolio.dev', 'creative-works.art'
  ];

  const threatLevels: Array<'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN'> = 
    ['SAFE', 'LOW', 'MEDIUM', 'HIGH', 'UNKNOWN'];
  
  const statuses: Array<'ACTIVE' | 'REMOVED' | 'INVESTIGATING'> = 
    ['ACTIVE', 'REMOVED', 'INVESTIGATING'];

  const riskFactorsPool = [
    '新規ドメイン（30日以内）',
    'SSL証明書なし',
    '著作権侵害の可能性',
    '検索順位が低い',
    'コンテンツ類似度が低い',
    '高い悪用リスク',
    '無許可商用利用',
    'メタデータ削除',
    '画像加工検出',
    'ウォーターマーク除去',
  ];

  // フィルターを適用してモックデータを生成
  const totalResults = Math.floor(Math.random() * 200) + 50;
  const results: SearchResult[] = [];

  for (let i = 0; i < Math.min(params.limit, totalResults - (params.page - 1) * params.limit); i++) {
    const domain = mockDomains[Math.floor(Math.random() * mockDomains.length)];
    const threatLevel = threatLevels[Math.floor(Math.random() * threatLevels.length)];
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const isOfficial = Math.random() < 0.2; // 20%の確率で公式

    // フィルターをチェック
    const passesFilter = (
      (params.filters.threatLevels.length === 0 || params.filters.threatLevels.includes(threatLevel)) &&
      (params.filters.domains.length === 0 || params.filters.domains.includes(domain)) &&
      (params.filters.status.length === 0 || params.filters.status.includes(status)) &&
      (params.filters.isOfficial === null || params.filters.isOfficial === isOfficial)
    );

    if (!passesFilter) continue;

    const similarityScore = Math.random() * 100;
    const threatScore = getThreatScore(threatLevel);
    const riskFactorCount = Math.floor(Math.random() * 4);
    const riskFactors = riskFactorsPool
      .sort(() => 0.5 - Math.random())
      .slice(0, riskFactorCount);

    results.push({
      id: `result-${i + (params.page - 1) * params.limit}`,
      imageId: params.imageId || `img-${Math.floor(Math.random() * 10000)}`,
      foundUrl: `https://${domain}/page${i + 1}`,
      domain,
      title: `Sample Content ${i + 1}`,
      description: `This is a sample description for search result ${i + 1}`,
      thumbnailUrl: `https://picsum.photos/200/200?random=${i}`,
      similarityScore,
      threatLevel,
      threatScore,
      isOfficial,
      detectedAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      lastChecked: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
      status,
      riskFactors,
      metadata: {
        pageTitle: `Sample Page ${i + 1}`,
        metaDescription: `Meta description for page ${i + 1}`,
        lastModified: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        language: 'ja',
        socialShares: Math.floor(Math.random() * 1000),
      },
      aiAnalysis: {
        contentAbuse: Math.random() * 100,
        copyrightRisk: Math.random() * 100,
        commercialUse: Math.random() < 0.3,
        unauthorizedRepost: Math.random() < 0.4,
      },
    });
  }

  return {
    results,
    total: totalResults,
    page: params.page,
    limit: params.limit,
    hasMore: (params.page * params.limit) < totalResults,
    totalPages: Math.ceil(totalResults / params.limit),
    facets: {
      domains: mockDomains.map(domain => ({
        domain,
        count: Math.floor(Math.random() * 50) + 1
      })),
      threatLevels: threatLevels.map(level => ({
        level,
        count: Math.floor(Math.random() * 30) + 1
      })),
      statuses: statuses.map(status => ({
        status,
        count: Math.floor(Math.random() * 40) + 1
      })),
    },
  };
};

// 脅威レベルに基づくスコア生成
const getThreatScore = (threatLevel: string): number => {
  switch (threatLevel) {
    case 'HIGH': return 80 + Math.random() * 20;
    case 'MEDIUM': return 50 + Math.random() * 30;
    case 'LOW': return 20 + Math.random() * 30;
    case 'SAFE': return Math.random() * 20;
    default: return Math.random() * 100;
  }
};

// ユーティリティ関数
export const formatSearchQuery = (query: string): string => {
  return query.trim().toLowerCase();
};

export const buildSearchUrl = (params: SearchParams): string => {
  const searchParams = new URLSearchParams();
  
  if (params.imageId) searchParams.append('imageId', params.imageId);
  if (params.query) searchParams.append('query', params.query);
  
  return `/search-results?${searchParams.toString()}`;
};

export const exportSearchResults = async (
  params: SearchParams,
  format: 'csv' | 'json' = 'csv'
): Promise<Blob> => {
  try {
    const response = await api.get(
      `/api/v1/search/export?format=${format}`,
      { 
        responseType: 'blob',
        ...params 
      }
    );
    return response as unknown as Blob;
  } catch (error) {
    console.error('Export search results error:', error);
    throw new Error('検索結果のエクスポートに失敗しました');
  }
}; 