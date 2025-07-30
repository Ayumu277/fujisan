import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Download,
  Eye,
  Grid,
  List,
  RefreshCw,
  AlertCircle,
  Info,
  TrendingUp,
  Clock,
  Shield,
} from 'lucide-react';
import toast from 'react-hot-toast';

import ResultCard, { SearchResult } from '../components/ResultCard';
import FilterPanel, { FilterConfig } from '../components/FilterPanel';
import {
  searchImages,
  getSearchStats,
  getAvailableDomains,
  exportSearchResults,
  updateSearchResultStatus,
  SearchParams,
  SearchStats,
} from '../services/searchService';

const SearchResults: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // 状態管理
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedResults, setSelectedResults] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // URLパラメータから初期フィルター設定を取得
  const initialFilters: FilterConfig = useMemo(() => ({
    threatLevels: searchParams.getAll('threatLevels'),
    domains: searchParams.getAll('domains'),
    dateRange: {
      startDate: searchParams.get('startDate'),
      endDate: searchParams.get('endDate'),
    },
    similarityRange: {
      min: parseInt(searchParams.get('minSimilarity') || '0'),
      max: parseInt(searchParams.get('maxSimilarity') || '100'),
    },
    status: searchParams.getAll('status'),
    isOfficial: searchParams.get('isOfficial') === 'true' ? true : 
                 searchParams.get('isOfficial') === 'false' ? false : null,
    hasRiskFactors: searchParams.get('hasRiskFactors') === 'true' ? true :
                    searchParams.get('hasRiskFactors') === 'false' ? false : null,
    sortBy: searchParams.get('sortBy') || 'detectedAt',
    sortOrder: (searchParams.get('sortOrder') as 'asc' | 'desc') || 'desc',
  }), [searchParams]);

  const [filters, setFilters] = useState<FilterConfig>(initialFilters);

  // 検索パラメータの構築
  const searchParameters: SearchParams = useMemo(() => ({
    imageId: searchParams.get('imageId') || undefined,
    query: searchParams.get('query') || undefined,
    filters,
    page: currentPage,
    limit: pageSize,
  }), [searchParams, filters, currentPage, pageSize]);

  // 検索結果の取得
  const {
    data: searchData,
    isLoading: isSearchLoading,
    error: searchError,
    refetch: refetchSearch,
  } = useQuery({
    queryKey: ['searchResults', searchParameters],
    queryFn: () => searchImages(searchParameters),
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30秒
  });

  // 検索統計の取得
  const {
    data: statsData,
    isLoading: isStatsLoading,
  } = useQuery({
    queryKey: ['searchStats', searchParameters.imageId],
    queryFn: () => getSearchStats(searchParameters.imageId),
    refetchOnWindowFocus: false,
    staleTime: 60000, // 1分
  });

  // 利用可能ドメインの取得
  const {
    data: availableDomains,
  } = useQuery({
    queryKey: ['availableDomains'],
    queryFn: getAvailableDomains,
    refetchOnWindowFocus: false,
    staleTime: 300000, // 5分
  });

  // フィルター変更時の処理
  const handleFiltersChange = useCallback((newFilters: FilterConfig) => {
    setFilters(newFilters);
    setCurrentPage(1); // フィルター変更時はページをリセット

    // URLパラメータを更新
    const newSearchParams = new URLSearchParams(searchParams);
    
    // 既存のフィルターパラメータをクリア
    ['threatLevels', 'domains', 'status'].forEach(key => {
      newSearchParams.delete(key);
    });
    ['startDate', 'endDate', 'minSimilarity', 'maxSimilarity', 'isOfficial', 'hasRiskFactors'].forEach(key => {
      newSearchParams.delete(key);
    });

    // 新しいフィルター値を設定
    newFilters.threatLevels.forEach(level => newSearchParams.append('threatLevels', level));
    newFilters.domains.forEach(domain => newSearchParams.append('domains', domain));
    newFilters.status.forEach(status => newSearchParams.append('status', status));

    if (newFilters.dateRange.startDate) newSearchParams.set('startDate', newFilters.dateRange.startDate);
    if (newFilters.dateRange.endDate) newSearchParams.set('endDate', newFilters.dateRange.endDate);
    if (newFilters.similarityRange.min > 0) newSearchParams.set('minSimilarity', newFilters.similarityRange.min.toString());
    if (newFilters.similarityRange.max < 100) newSearchParams.set('maxSimilarity', newFilters.similarityRange.max.toString());
    if (newFilters.isOfficial !== null) newSearchParams.set('isOfficial', newFilters.isOfficial.toString());
    if (newFilters.hasRiskFactors !== null) newSearchParams.set('hasRiskFactors', newFilters.hasRiskFactors.toString());

    newSearchParams.set('sortBy', newFilters.sortBy);
    newSearchParams.set('sortOrder', newFilters.sortOrder);

    setSearchParams(newSearchParams);
  }, [searchParams, setSearchParams]);

  // ページ変更
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // スクロールトップ
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 結果詳細表示
  const handleViewDetails = useCallback((result: SearchResult) => {
    navigate(`/search-results/${result.id}`, { 
      state: { result, backUrl: window.location.pathname + window.location.search }
    });
  }, [navigate]);

  // 元ページを新しいタブで開く
  const handleViewOriginal = useCallback((url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  // 検索結果エクスポート
  const handleExport = useCallback(async (format: 'csv' | 'json' = 'csv') => {
    try {
      const blob = await exportSearchResults(searchParameters, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `search-results-${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('検索結果をエクスポートしました');
    } catch (error) {
      toast.error('エクスポートに失敗しました');
    }
  }, [searchParameters]);

  // 結果ステータス更新
  const handleUpdateStatus = useCallback(async (
    resultId: string, 
    status: 'ACTIVE' | 'REMOVED' | 'INVESTIGATING'
  ) => {
    try {
      await updateSearchResultStatus(resultId, status);
      await refetchSearch();
      toast.success('ステータスを更新しました');
    } catch (error) {
      toast.error('ステータスの更新に失敗しました');
    }
  }, [refetchSearch]);

  // エラー状態の処理
  if (searchError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            検索結果の取得に失敗しました
          </h2>
          <p className="text-gray-600 mb-4">
            {searchError instanceof Error ? searchError.message : 'ネットワークエラーが発生しました'}
          </p>
          <button
            onClick={() => refetchSearch()}
            className="btn-primary"
          >
            再試行
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">検索結果</h1>
              <p className="text-gray-600 mt-1">
                {searchParameters.imageId ? '画像' : 'クエリ'}「
                {searchParameters.imageId || searchParameters.query || '全体'}
                」の検索結果
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* 表示モード切替 */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded transition-colors ${
                    viewMode === 'grid' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  title="グリッド表示"
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded transition-colors ${
                    viewMode === 'list' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  title="リスト表示"
                >
                  <List className="w-4 h-4" />
                </button>
              </div>

              {/* アクションボタン */}
              <button
                onClick={() => refetchSearch()}
                disabled={isSearchLoading}
                className="p-2 text-gray-400 hover:text-blue-600 transition-colors disabled:opacity-50"
                title="更新"
              >
                <RefreshCw className={`w-4 h-4 ${isSearchLoading ? 'animate-spin' : ''}`} />
              </button>

              <button
                onClick={() => handleExport('csv')}
                className="btn-outline text-sm"
                title="CSVエクスポート"
              >
                <Download className="w-4 h-4 mr-2" />
                エクスポート
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* フィルターパネル */}
          <div className="lg:col-span-1">
            <FilterPanel
              filters={filters}
              onFiltersChange={handleFiltersChange}
              availableDomains={availableDomains || []}
              resultCount={searchData?.total || 0}
              isLoading={isSearchLoading}
            />

            {/* 統計情報 */}
            {statsData && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-6">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">検索統計</h3>
                </div>
                <div className="p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">総結果数</span>
                    <span className="text-lg font-semibold text-gray-900">
                      {statsData.totalResults.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">平均脅威スコア</span>
                    <span className="text-lg font-semibold text-orange-600">
                      {statsData.averageThreatScore.toFixed(1)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">高リスク検出</span>
                    <span className="text-lg font-semibold text-red-600">
                      {statsData.highRiskCount}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">監視中</span>
                    <span className="text-lg font-semibold text-blue-600">
                      {statsData.activeMonitoring}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* メインコンテンツ */}
          <div className="lg:col-span-3">
            {/* 結果ヘッダー */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <Search className="w-4 h-4" />
                    <span>
                      {searchData?.total.toLocaleString() || 0}件中 
                      {Math.min((currentPage - 1) * pageSize + 1, searchData?.total || 0)} - 
                      {Math.min(currentPage * pageSize, searchData?.total || 0)}件を表示
                    </span>
                  </div>
                  {isSearchLoading && (
                    <div className="flex items-center space-x-2 text-sm text-blue-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span>検索中...</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-3">
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(parseInt(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="input text-sm"
                  >
                    <option value={10}>10件</option>
                    <option value={20}>20件</option>
                    <option value={50}>50件</option>
                    <option value={100}>100件</option>
                  </select>
                </div>
              </div>
            </div>

            {/* 検索結果 */}
            {isSearchLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg border border-gray-200 p-6">
                    <div className="animate-pulse">
                      <div className="flex space-x-4">
                        <div className="w-24 h-24 bg-gray-200 rounded-lg"></div>
                        <div className="flex-1 space-y-2">
                          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : searchData?.results.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  検索結果が見つかりませんでした
                </h3>
                <p className="text-gray-600 mb-4">
                  フィルター条件を変更するか、別のキーワードで検索してください。
                </p>
                <button
                  onClick={() => setFilters({
                    threatLevels: [],
                    domains: [],
                    dateRange: { startDate: null, endDate: null },
                    similarityRange: { min: 0, max: 100 },
                    status: [],
                    isOfficial: null,
                    hasRiskFactors: null,
                    sortBy: 'detectedAt',
                    sortOrder: 'desc',
                  })}
                  className="btn-outline"
                >
                  フィルターをリセット
                </button>
              </div>
            ) : (
              <>
                {/* 結果グリッド/リスト */}
                <div className={
                  viewMode === 'grid' 
                    ? 'grid grid-cols-1 md:grid-cols-2 gap-6'
                    : 'space-y-4'
                }>
                  {searchData?.results.map((result) => (
                    <ResultCard
                      key={result.id}
                      result={result}
                      onViewDetails={handleViewDetails}
                      onViewOriginal={handleViewOriginal}
                      compact={viewMode === 'list'}
                    />
                  ))}
                </div>

                {/* ページネーション */}
                {searchData && searchData.totalPages > 1 && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={currentPage === 1}
                          className="px-3 py-2 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
                        >
                          前へ
                        </button>
                        
                        <div className="flex items-center space-x-1">
                          {Array.from({ length: Math.min(5, searchData.totalPages) }, (_, i) => {
                            const pageNum = Math.max(1, Math.min(searchData.totalPages - 4, currentPage - 2)) + i;
                            return (
                              <button
                                key={pageNum}
                                onClick={() => handlePageChange(pageNum)}
                                className={`px-3 py-2 text-sm rounded-md transition-colors ${
                                  pageNum === currentPage
                                    ? 'bg-blue-600 text-white'
                                    : 'border border-gray-300 hover:bg-gray-50'
                                }`}
                              >
                                {pageNum}
                              </button>
                            );
                          })}
                        </div>

                        <button
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={currentPage === searchData.totalPages}
                          className="px-3 py-2 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
                        >
                          次へ
                        </button>
                      </div>

                      <div className="text-sm text-gray-600">
                        ページ {currentPage} / {searchData.totalPages}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchResults; 