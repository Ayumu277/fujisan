import React, { useState, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Filter,
  Download,
  Upload,
  Trash2,
  Edit,
  Check,
  X,
  AlertTriangle,
  Globe,
  Calendar,
  User,
  MoreVertical,
  FileText,
  Copy,
  ExternalLink,
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

// ホワイトリストドメインの型定義
export interface WhitelistDomain {
  id: string;
  domain: string;
  addedBy: string;
  addedAt: string;
  description?: string;
  isActive: boolean;
  category: 'official' | 'partner' | 'trusted' | 'other';
  verifiedAt?: string;
  verifiedBy?: string;
}

// API応答の型定義
interface WhitelistResponse {
  domains: WhitelistDomain[];
  total: number;
  page: number;
  limit: number;
}

// フィルター設定の型定義
interface FilterOptions {
  search: string;
  category: string;
  isActive: boolean | null;
  dateRange: {
    from: string;
    to: string;
  };
}

// インポートデータの型定義
interface ImportData {
  domain: string;
  category?: string;
  description?: string;
}

// WhitelistManagerの props
interface WhitelistManagerProps {
  className?: string;
  onDomainSelect?: (domain: WhitelistDomain) => void;
}

// モックAPI関数（実際のAPIに置き換える）
const mockWhitelistAPI = {
  getWhitelistDomains: async (page = 1, limit = 20, filters: Partial<FilterOptions> = {}) => {
    // モックデータ生成
    const mockDomains: WhitelistDomain[] = Array.from({ length: 15 }, (_, i) => ({
      id: `domain-${i + 1}`,
      domain: `${['example', 'trusted', 'official', 'partner', 'secure'][i % 5]}-${i + 1}.com`,
      addedBy: ['管理者', '運営者', 'セキュリティチーム'][i % 3],
      addedAt: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString(),
      description: ['公式サイト', '信頼できるパートナー', '認証済みドメイン', '内部サービス'][i % 4],
      isActive: Math.random() > 0.2,
      category: (['official', 'partner', 'trusted', 'other'] as const)[i % 4],
      verifiedAt: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString() : undefined,
      verifiedBy: Math.random() > 0.3 ? 'セキュリティチーム' : undefined,
    })).filter(domain => {
      if (filters.search && !domain.domain.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }
      if (filters.category && filters.category !== 'all' && domain.category !== filters.category) {
        return false;
      }
      if (filters.isActive !== null && domain.isActive !== filters.isActive) {
        return false;
      }
      return true;
    });

    return {
      domains: mockDomains.slice((page - 1) * limit, page * limit),
      total: mockDomains.length,
      page,
      limit,
    };
  },

  addDomain: async (domain: Omit<WhitelistDomain, 'id' | 'addedAt'>) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { id: `domain-${Date.now()}`, ...domain, addedAt: new Date().toISOString() };
  },

  updateDomain: async (id: string, updates: Partial<WhitelistDomain>) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { id, ...updates };
  },

  deleteDomains: async (ids: string[]) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { deletedCount: ids.length };
  },

  importDomains: async (domains: ImportData[]) => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return { imported: domains.length, errors: [] };
  },

  exportDomains: async (filters: Partial<FilterOptions> = {}) => {
    const { domains } = await mockWhitelistAPI.getWhitelistDomains(1, 1000, filters);
    return domains;
  },
};

export const WhitelistManager: React.FC<WhitelistManagerProps> = ({
  className = '',
  onDomainSelect,
}) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 状態管理
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState<FilterOptions>({
    search: '',
    category: 'all',
    isActive: null,
    dateRange: { from: '', to: '' },
  });
  const [selectedDomains, setSelectedDomains] = useState<Set<string>>(new Set());
  const [editingDomain, setEditingDomain] = useState<WhitelistDomain | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newDomain, setNewDomain] = useState({
    domain: '',
    category: 'other' as WhitelistDomain['category'],
    description: '',
    isActive: true,
    addedBy: 'Current User',
  });

  // データ取得
  const {
    data: whitelistData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['whitelistDomains', currentPage, pageSize, filters],
    queryFn: () => mockWhitelistAPI.getWhitelistDomains(currentPage, pageSize, filters),
    refetchOnWindowFocus: false,
  });

  // ミューテーション
  const addMutation = useMutation({
    mutationFn: mockWhitelistAPI.addDomain,
    onSuccess: () => {
      toast.success('ドメインを追加しました');
      setShowAddForm(false);
      setNewDomain({
        domain: '',
        category: 'other',
        description: '',
        isActive: true,
        addedBy: 'Current User',
      });
      queryClient.invalidateQueries({ queryKey: ['whitelistDomains'] });
    },
    onError: () => {
      toast.error('ドメインの追加に失敗しました');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<WhitelistDomain> }) =>
      mockWhitelistAPI.updateDomain(id, updates),
    onSuccess: () => {
      toast.success('ドメインを更新しました');
      setEditingDomain(null);
      queryClient.invalidateQueries({ queryKey: ['whitelistDomains'] });
    },
    onError: () => {
      toast.error('ドメインの更新に失敗しました');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: mockWhitelistAPI.deleteDomains,
    onSuccess: (data) => {
      toast.success(`${data.deletedCount}個のドメインを削除しました`);
      setSelectedDomains(new Set());
      queryClient.invalidateQueries({ queryKey: ['whitelistDomains'] });
    },
    onError: () => {
      toast.error('ドメインの削除に失敗しました');
    },
  });

  const importMutation = useMutation({
    mutationFn: mockWhitelistAPI.importDomains,
    onSuccess: (data) => {
      toast.success(`${data.imported}個のドメインをインポートしました`);
      queryClient.invalidateQueries({ queryKey: ['whitelistDomains'] });
    },
    onError: () => {
      toast.error('ドメインのインポートに失敗しました');
    },
  });

  // カテゴリ設定
  const categoryConfig = {
    official: { label: '公式', color: 'bg-green-100 text-green-800', icon: Check },
    partner: { label: 'パートナー', color: 'bg-blue-100 text-blue-800', icon: Globe },
    trusted: { label: '信頼済み', color: 'bg-yellow-100 text-yellow-800', icon: User },
    other: { label: 'その他', color: 'bg-gray-100 text-gray-800', icon: MoreVertical },
  };

  // ハンドラー関数
  const handleSelectAll = useCallback(() => {
    if (!whitelistData) return;

    const allIds = whitelistData.domains.map(d => d.id);
    const allSelected = allIds.every(id => selectedDomains.has(id));

    if (allSelected) {
      setSelectedDomains(new Set());
    } else {
      setSelectedDomains(new Set(allIds));
    }
  }, [whitelistData, selectedDomains]);

  const handleSelectDomain = useCallback((id: string) => {
    setSelectedDomains(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  const handleAddDomain = useCallback(() => {
    if (!newDomain.domain.trim()) {
      toast.error('ドメイン名を入力してください');
      return;
    }

    // 簡単なドメイン形式チェック
    const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    if (!domainRegex.test(newDomain.domain)) {
      toast.error('有効なドメイン名を入力してください');
      return;
    }

    addMutation.mutate(newDomain);
  }, [newDomain, addMutation]);

  const handleUpdateDomain = useCallback((domain: WhitelistDomain) => {
    if (!domain.domain.trim()) {
      toast.error('ドメイン名を入力してください');
      return;
    }

    updateMutation.mutate({
      id: domain.id,
      updates: {
        domain: domain.domain,
        category: domain.category,
        description: domain.description,
        isActive: domain.isActive,
      },
    });
  }, [updateMutation]);

  const handleDeleteSelected = useCallback(() => {
    if (selectedDomains.size === 0) {
      toast.error('削除するドメインを選択してください');
      return;
    }

    if (window.confirm(`${selectedDomains.size}個のドメインを削除しますか？`)) {
      deleteMutation.mutate(Array.from(selectedDomains));
    }
  }, [selectedDomains, deleteMutation]);

  const handleExport = useCallback(async () => {
    try {
      const domains = await mockWhitelistAPI.exportDomains(filters);
      const csvContent = [
        ['ドメイン', 'カテゴリ', '説明', 'ステータス', '追加者', '追加日'],
        ...domains.map(d => [
          d.domain,
          categoryConfig[d.category].label,
          d.description || '',
          d.isActive ? 'アクティブ' : '無効',
          d.addedBy,
          format(new Date(d.addedAt), 'yyyy/MM/dd'),
        ]),
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `whitelist-domains-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      link.click();
      URL.revokeObjectURL(link.href);

      toast.success('ホワイトリストをエクスポートしました');
    } catch (error) {
      toast.error('エクスポートに失敗しました');
    }
  }, [filters, categoryConfig]);

  const handleImport = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csv = e.target?.result as string;
        const lines = csv.split('\n');
        const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());

        const domains: ImportData[] = lines.slice(1)
          .filter(line => line.trim())
          .map(line => {
            const values = line.split(',').map(v => v.replace(/"/g, '').trim());
            return {
              domain: values[0],
              category: values[1] === '公式' ? 'official' :
                       values[1] === 'パートナー' ? 'partner' :
                       values[1] === '信頼済み' ? 'trusted' : 'other',
              description: values[2] || '',
            };
          })
          .filter(d => d.domain);

        if (domains.length === 0) {
          toast.error('有効なドメインが見つかりませんでした');
          return;
        }

        importMutation.mutate(domains);
      } catch (error) {
        toast.error('ファイルの読み込みに失敗しました');
      }
    };
    reader.readAsText(file);

    // ファイル入力をリセット
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [importMutation]);

  const handleFilterChange = useCallback((key: keyof FilterOptions, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  }, []);

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* ヘッダー */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">ホワイトリスト管理</h3>
            <p className="text-sm text-gray-600 mt-1">
              信頼できるドメインを管理します
              {whitelistData && (
                <span className="ml-2">
                  ({whitelistData.total}個のドメイン)
                </span>
              )}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAddForm(true)}
              className="btn-primary text-sm"
            >
              <Plus className="w-4 h-4 mr-2" />
              ドメイン追加
            </button>

            <div className="flex items-center space-x-1">
              <button
                onClick={handleExport}
                className="btn-outline text-sm"
                title="エクスポート"
              >
                <Download className="w-4 h-4" />
              </button>

              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-outline text-sm"
                title="インポート"
              >
                <Upload className="w-4 h-4" />
              </button>

              {selectedDomains.size > 0 && (
                <button
                  onClick={handleDeleteSelected}
                  className="btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50"
                  title="選択項目を削除"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* フィルター */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="ドメイン検索..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 input text-sm"
            />
          </div>

          <select
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
            className="input text-sm"
          >
            <option value="all">すべてのカテゴリ</option>
            <option value="official">公式</option>
            <option value="partner">パートナー</option>
            <option value="trusted">信頼済み</option>
            <option value="other">その他</option>
          </select>

          <select
            value={filters.isActive === null ? 'all' : filters.isActive.toString()}
            onChange={(e) => handleFilterChange('isActive',
              e.target.value === 'all' ? null : e.target.value === 'true'
            )}
            className="input text-sm"
          >
            <option value="all">すべてのステータス</option>
            <option value="true">アクティブ</option>
            <option value="false">無効</option>
          </select>

          <div className="flex items-center text-sm text-gray-600">
            {selectedDomains.size > 0 && (
              <span>{selectedDomains.size}個選択中</span>
            )}
          </div>
        </div>
      </div>

      {/* コンテンツ */}
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">読み込み中...</span>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              データの取得に失敗しました
            </h3>
            <button onClick={() => refetch()} className="btn-primary">
              再試行
            </button>
          </div>
        ) : (
          <>
            {/* ドメインリスト */}
            <div className="space-y-2">
              {/* ヘッダー */}
              <div className="flex items-center py-2 px-4 bg-gray-50 rounded-lg text-sm font-medium text-gray-700">
                <div className="w-8">
                  <input
                    type="checkbox"
                    checked={whitelistData?.domains.length > 0 &&
                            whitelistData.domains.every(d => selectedDomains.has(d.id))}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
                <div className="flex-1">ドメイン</div>
                <div className="w-24">カテゴリ</div>
                <div className="w-20">ステータス</div>
                <div className="w-28">追加日</div>
                <div className="w-16">操作</div>
              </div>

              {/* ドメイン項目 */}
              {whitelistData?.domains.map((domain) => (
                <div
                  key={domain.id}
                  className={`flex items-center py-3 px-4 border rounded-lg transition-colors ${
                    selectedDomains.has(domain.id)
                      ? 'bg-blue-50 border-blue-200'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="w-8">
                    <input
                      type="checkbox"
                      checked={selectedDomains.has(domain.id)}
                      onChange={() => handleSelectDomain(domain.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex-1">
                    {editingDomain?.id === domain.id ? (
                      <input
                        type="text"
                        value={editingDomain.domain}
                        onChange={(e) => setEditingDomain(prev =>
                          prev ? { ...prev, domain: e.target.value } : null
                        )}
                        className="input text-sm w-full max-w-xs"
                        autoFocus
                      />
                    ) : (
                      <div>
                        <div className="font-medium text-gray-900">{domain.domain}</div>
                        {domain.description && (
                          <div className="text-xs text-gray-500 mt-1">{domain.description}</div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="w-24">
                    {editingDomain?.id === domain.id ? (
                      <select
                        value={editingDomain.category}
                        onChange={(e) => setEditingDomain(prev =>
                          prev ? { ...prev, category: e.target.value as WhitelistDomain['category'] } : null
                        )}
                        className="input text-xs w-full"
                      >
                        <option value="official">公式</option>
                        <option value="partner">パートナー</option>
                        <option value="trusted">信頼済み</option>
                        <option value="other">その他</option>
                      </select>
                    ) : (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        categoryConfig[domain.category].color
                      }`}>
                        {categoryConfig[domain.category].label}
                      </span>
                    )}
                  </div>

                  <div className="w-20">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      domain.isActive
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {domain.isActive ? 'アクティブ' : '無効'}
                    </span>
                  </div>

                  <div className="w-28 text-xs text-gray-500">
                    {format(new Date(domain.addedAt), 'yyyy/MM/dd')}
                  </div>

                  <div className="w-16 flex items-center space-x-1">
                    {editingDomain?.id === domain.id ? (
                      <>
                        <button
                          onClick={() => handleUpdateDomain(editingDomain)}
                          disabled={updateMutation.isPending}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                          title="保存"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setEditingDomain(null)}
                          className="p-1 text-gray-400 hover:bg-gray-50 rounded"
                          title="キャンセル"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => setEditingDomain(domain)}
                        className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="編集"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* ページネーション */}
            {whitelistData && whitelistData.total > pageSize && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-700">
                  {whitelistData.total}件中 {((currentPage - 1) * pageSize) + 1}-
                  {Math.min(currentPage * pageSize, whitelistData.total)}件を表示
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="btn-outline text-sm disabled:opacity-50"
                  >
                    前へ
                  </button>
                  <span className="text-sm text-gray-700">
                    {currentPage} / {Math.ceil(whitelistData.total / pageSize)}
                  </span>
                  <button
                    onClick={() => setCurrentPage(prev =>
                      Math.min(Math.ceil(whitelistData.total / pageSize), prev + 1)
                    )}
                    disabled={currentPage >= Math.ceil(whitelistData.total / pageSize)}
                    className="btn-outline text-sm disabled:opacity-50"
                  >
                    次へ
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* 新規追加フォーム */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">新しいドメインを追加</h3>
              <button
                onClick={() => setShowAddForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">ドメイン名 *</label>
                <input
                  type="text"
                  value={newDomain.domain}
                  onChange={(e) => setNewDomain(prev => ({ ...prev, domain: e.target.value }))}
                  placeholder="example.com"
                  className="input"
                  autoFocus
                />
              </div>

              <div>
                <label className="label">カテゴリ</label>
                <select
                  value={newDomain.category}
                  onChange={(e) => setNewDomain(prev => ({
                    ...prev,
                    category: e.target.value as WhitelistDomain['category']
                  }))}
                  className="input"
                >
                  <option value="official">公式</option>
                  <option value="partner">パートナー</option>
                  <option value="trusted">信頼済み</option>
                  <option value="other">その他</option>
                </select>
              </div>

              <div>
                <label className="label">説明</label>
                <textarea
                  value={newDomain.description}
                  onChange={(e) => setNewDomain(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="このドメインについての説明..."
                  className="input"
                  rows={3}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={newDomain.isActive}
                  onChange={(e) => setNewDomain(prev => ({ ...prev, isActive: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="isActive" className="ml-2 text-sm text-gray-700">
                  アクティブ状態で追加
                </label>
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleAddDomain}
                disabled={addMutation.isPending}
                className="btn-primary flex-1 disabled:opacity-50"
              >
                {addMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    追加中...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    追加
                  </>
                )}
              </button>
              <button
                onClick={() => setShowAddForm(false)}
                className="btn-outline flex-1"
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 隠しファイル入力 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleImport}
        className="hidden"
      />
    </div>
  );
};

export default WhitelistManager;