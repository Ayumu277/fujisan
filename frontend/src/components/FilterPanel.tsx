import React, { useState, useCallback } from 'react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import {
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  Calendar,
  Shield,
  Globe,
  Search,
  RotateCcw,
} from 'lucide-react';

// フィルター設定の型定義
export interface FilterConfig {
  threatLevels: string[];
  domains: string[];
  dateRange: {
    startDate: string | null;
    endDate: string | null;
  };
  similarityRange: {
    min: number;
    max: number;
  };
  status: string[];
  isOfficial: boolean | null;
  hasRiskFactors: boolean | null;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

interface FilterPanelProps {
  filters: FilterConfig;
  onFiltersChange: (filters: FilterConfig) => void;
  availableDomains: string[];
  resultCount: number;
  isLoading?: boolean;
  className?: string;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  availableDomains,
  resultCount,
  isLoading = false,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [domainSearch, setDomainSearch] = useState('');

  // 脅威レベルの定義
  const threatLevels = [
    { value: 'HIGH', label: '高リスク', color: 'text-red-600 bg-red-50' },
    { value: 'MEDIUM', label: '中リスク', color: 'text-orange-600 bg-orange-50' },
    { value: 'LOW', label: '低リスク', color: 'text-yellow-600 bg-yellow-50' },
    { value: 'SAFE', label: '安全', color: 'text-green-600 bg-green-50' },
    { value: 'UNKNOWN', label: '不明', color: 'text-gray-600 bg-gray-50' },
  ];

  // ステータスの定義
  const statusOptions = [
    { value: 'ACTIVE', label: 'アクティブ' },
    { value: 'REMOVED', label: '削除済み' },
    { value: 'INVESTIGATING', label: '調査中' },
  ];

  // ソートオプション
  const sortOptions = [
    { value: 'detectedAt', label: '検出日時' },
    { value: 'threatScore', label: '脅威スコア' },
    { value: 'similarityScore', label: '類似度' },
    { value: 'domain', label: 'ドメイン' },
    { value: 'lastChecked', label: '最終確認' },
  ];

  // 事前定義された日付範囲
  const quickDateRanges = [
    { label: '今日', days: 0 },
    { label: '過去3日', days: 3 },
    { label: '過去1週間', days: 7 },
    { label: '過去1ヶ月', days: 30 },
    { label: '過去3ヶ月', days: 90 },
  ];

  // フィルター更新関数
  const updateFilter = useCallback((key: keyof FilterConfig, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  }, [filters, onFiltersChange]);

  // 脅威レベルフィルターの切り替え
  const toggleThreatLevel = (level: string) => {
    const currentLevels = filters.threatLevels;
    const newLevels = currentLevels.includes(level)
      ? currentLevels.filter(l => l !== level)
      : [...currentLevels, level];
    updateFilter('threatLevels', newLevels);
  };

  // ドメインフィルターの切り替え
  const toggleDomain = (domain: string) => {
    const currentDomains = filters.domains;
    const newDomains = currentDomains.includes(domain)
      ? currentDomains.filter(d => d !== domain)
      : [...currentDomains, domain];
    updateFilter('domains', newDomains);
  };

  // ステータスフィルターの切り替え
  const toggleStatus = (status: string) => {
    const currentStatus = filters.status;
    const newStatus = currentStatus.includes(status)
      ? currentStatus.filter(s => s !== status)
      : [...currentStatus, status];
    updateFilter('status', newStatus);
  };

  // クイック日付範囲の設定
  const setQuickDateRange = (days: number) => {
    const endDate = endOfDay(new Date());
    const startDate = days === 0 ? startOfDay(new Date()) : startOfDay(subDays(new Date(), days));
    
    updateFilter('dateRange', {
      startDate: format(startDate, 'yyyy-MM-dd'),
      endDate: format(endDate, 'yyyy-MM-dd'),
    });
  };

  // フィルターのリセット
  const resetFilters = () => {
    onFiltersChange({
      threatLevels: [],
      domains: [],
      dateRange: { startDate: null, endDate: null },
      similarityRange: { min: 0, max: 100 },
      status: [],
      isOfficial: null,
      hasRiskFactors: null,
      sortBy: 'detectedAt',
      sortOrder: 'desc',
    });
  };

  // ドメイン検索でフィルタリング
  const filteredDomains = availableDomains.filter(domain =>
    domain.toLowerCase().includes(domainSearch.toLowerCase())
  );

  // アクティブフィルターの数を計算
  const activeFilterCount = [
    filters.threatLevels.length > 0,
    filters.domains.length > 0,
    filters.dateRange.startDate || filters.dateRange.endDate,
    filters.status.length > 0,
    filters.isOfficial !== null,
    filters.hasRiskFactors !== null,
    filters.similarityRange.min > 0 || filters.similarityRange.max < 100,
  ].filter(Boolean).length;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* ヘッダー */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Filter className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">フィルター</h3>
              <p className="text-sm text-gray-500">
                {resultCount.toLocaleString()}件の結果
                {activeFilterCount > 0 && ` (${activeFilterCount}個のフィルター適用中)`}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {activeFilterCount > 0 && (
              <button
                onClick={resetFilters}
                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                title="フィルターをリセット"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* フィルター内容 */}
      {isExpanded && (
        <div className="p-4 space-y-6">
          {/* ソート設定 */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">並び順</h4>
            <div className="flex space-x-3">
              <select
                value={filters.sortBy}
                onChange={(e) => updateFilter('sortBy', e.target.value)}
                className="flex-1 input text-sm"
              >
                {sortOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select
                value={filters.sortOrder}
                onChange={(e) => updateFilter('sortOrder', e.target.value)}
                className="input text-sm"
              >
                <option value="desc">降順</option>
                <option value="asc">昇順</option>
              </select>
            </div>
          </div>

          {/* 脅威レベルフィルター */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">脅威レベル</h4>
            <div className="space-y-2">
              {threatLevels.map(level => (
                <label key={level.value} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.threatLevels.includes(level.value)}
                    onChange={() => toggleThreatLevel(level.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className={`flex items-center space-x-2 px-2 py-1 rounded text-sm font-medium ${level.color}`}>
                    <Shield className="w-3 h-3" />
                    <span>{level.label}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* ステータスフィルター */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">ステータス</h4>
            <div className="space-y-2">
              {statusOptions.map(status => (
                <label key={status.value} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.status.includes(status.value)}
                    onChange={() => toggleStatus(status.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{status.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 類似度範囲 */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              類似度範囲 ({filters.similarityRange.min}% - {filters.similarityRange.max}%)
            </h4>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500">最小値</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.similarityRange.min}
                  onChange={(e) => updateFilter('similarityRange', {
                    ...filters.similarityRange,
                    min: parseInt(e.target.value)
                  })}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">最大値</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.similarityRange.max}
                  onChange={(e) => updateFilter('similarityRange', {
                    ...filters.similarityRange,
                    max: parseInt(e.target.value)
                  })}
                  className="w-full"
                />
              </div>
            </div>
          </div>

          {/* 日付範囲フィルター */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">検出日時</h4>
            
            {/* クイック選択 */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              {quickDateRanges.map(range => (
                <button
                  key={range.days}
                  onClick={() => setQuickDateRange(range.days)}
                  className="px-3 py-2 text-xs bg-gray-50 hover:bg-gray-100 rounded border text-gray-700 transition-colors"
                >
                  {range.label}
                </button>
              ))}
            </div>

            {/* カスタム日付選択 */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">開始日</label>
                <input
                  type="date"
                  value={filters.dateRange.startDate || ''}
                  onChange={(e) => updateFilter('dateRange', {
                    ...filters.dateRange,
                    startDate: e.target.value || null
                  })}
                  className="input text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">終了日</label>
                <input
                  type="date"
                  value={filters.dateRange.endDate || ''}
                  onChange={(e) => updateFilter('dateRange', {
                    ...filters.dateRange,
                    endDate: e.target.value || null
                  })}
                  className="input text-sm"
                />
              </div>
            </div>
          </div>

          {/* ドメインフィルター */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">ドメイン</h4>
            
            {/* ドメイン検索 */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="ドメインを検索..."
                value={domainSearch}
                onChange={(e) => setDomainSearch(e.target.value)}
                className="input pl-10 text-sm"
              />
            </div>

            {/* ドメインリスト */}
            <div className="max-h-48 overflow-y-auto space-y-2">
              {filteredDomains.slice(0, 20).map(domain => (
                <label key={domain} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.domains.includes(domain)}
                    onChange={() => toggleDomain(domain)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex items-center space-x-2 text-sm text-gray-700">
                    <Globe className="w-3 h-3 text-gray-400" />
                    <span className="truncate">{domain}</span>
                  </div>
                </label>
              ))}
              {filteredDomains.length > 20 && (
                <p className="text-xs text-gray-500 text-center py-2">
                  他 {filteredDomains.length - 20} 件...
                </p>
              )}
            </div>
          </div>

          {/* その他のフィルター */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">その他</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">公式サイトのみ</span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => updateFilter('isOfficial', true)}
                    className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                      filters.isOfficial === true
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    はい
                  </button>
                  <button
                    onClick={() => updateFilter('isOfficial', false)}
                    className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                      filters.isOfficial === false
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    いいえ
                  </button>
                  <button
                    onClick={() => updateFilter('isOfficial', null)}
                    className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                      filters.isOfficial === null
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    全て
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">リスク要因あり</span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => updateFilter('hasRiskFactors', true)}
                    className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                      filters.hasRiskFactors === true
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    はい
                  </button>
                  <button
                    onClick={() => updateFilter('hasRiskFactors', false)}
                    className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                      filters.hasRiskFactors === false
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    いいえ
                  </button>
                  <button
                    onClick={() => updateFilter('hasRiskFactors', null)}
                    className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                      filters.hasRiskFactors === null
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    全て
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ローディング状態 */}
      {isLoading && (
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>フィルター適用中...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel; 