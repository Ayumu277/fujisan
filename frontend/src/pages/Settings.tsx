import React, { useState, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings as SettingsIcon,
  Shield,
  Bell,
  Key,
  Globe,
  Server,
  Save,
  RefreshCw,
  Download,
  Upload,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  TestTube,
  History,
  RotateCcw,
  Info,
  X,
} from 'lucide-react';
import toast from 'react-hot-toast';

import WhitelistManager from '../components/WhitelistManager';
import {
  SettingsService,
  ThresholdSettings,
  NotificationSettings,
  APIKeySettings,
  SystemSettings,
  AllSettings,
  maskAPIKey,
  validateThresholds,
  validateNotificationSettings,
} from '../services/settingsService';

const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 状態管理
  const [activeTab, setActiveTab] = useState<'whitelist' | 'thresholds' | 'notifications' | 'apikeys' | 'system'>('whitelist');
  const [showAPIKeys, setShowAPIKeys] = useState<Record<string, boolean>>({});
  const [validatingKeys, setValidatingKeys] = useState<Record<string, boolean>>({});
  const [testingNotifications, setTestingNotifications] = useState<Record<string, boolean>>({});

  // 設定データの取得
  const {
    data: settings,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['settings'],
    queryFn: SettingsService.getAllSettings,
    refetchOnWindowFocus: false,
  });

  // ミューテーション
  const updateThresholdsMutation = useMutation({
    mutationFn: SettingsService.updateThresholds,
    onSuccess: () => {
      toast.success('しきい値設定を保存しました');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => {
      toast.error('しきい値設定の保存に失敗しました');
    },
  });

  const updateNotificationsMutation = useMutation({
    mutationFn: SettingsService.updateNotifications,
    onSuccess: () => {
      toast.success('通知設定を保存しました');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => {
      toast.error('通知設定の保存に失敗しました');
    },
  });

  const updateAPIKeysMutation = useMutation({
    mutationFn: SettingsService.updateAPIKeys,
    onSuccess: () => {
      toast.success('APIキー設定を保存しました');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => {
      toast.error('APIキー設定の保存に失敗しました');
    },
  });

  const updateSystemMutation = useMutation({
    mutationFn: SettingsService.updateSystemSettings,
    onSuccess: () => {
      toast.success('システム設定を保存しました');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: () => {
      toast.error('システム設定の保存に失敗しました');
    },
  });

  // しきい値設定の保存
  const handleSaveThresholds = useCallback((thresholds: ThresholdSettings) => {
    const errors = validateThresholds(thresholds);
    if (errors.length > 0) {
      toast.error(errors[0]);
      return;
    }
    updateThresholdsMutation.mutate(thresholds);
  }, [updateThresholdsMutation]);

  // 通知設定の保存
  const handleSaveNotifications = useCallback((notifications: NotificationSettings) => {
    const errors = validateNotificationSettings(notifications);
    if (errors.length > 0) {
      toast.error(errors[0]);
      return;
    }
    updateNotificationsMutation.mutate(notifications);
  }, [updateNotificationsMutation]);

  // APIキーの検証
  const handleValidateAPIKey = useCallback(async (provider: keyof APIKeySettings, key: string) => {
    if (!key.trim()) {
      toast.error('APIキーを入力してください');
      return;
    }

    setValidatingKeys(prev => ({ ...prev, [provider]: true }));
    try {
      const result = await SettingsService.validateAPIKey(provider, key);
      if (result.isValid) {
        toast.success('APIキーの検証が完了しました');
        // 設定を更新
        if (settings) {
          const updatedAPIKeys = {
            ...settings.apiKeys,
            [provider]: {
              ...settings.apiKeys[provider],
              key,
              isValid: true,
              lastValidated: new Date().toISOString(),
              usage: result.usage,
            },
          };
          updateAPIKeysMutation.mutate(updatedAPIKeys);
        }
      } else {
        toast.error(result.error || 'APIキーの検証に失敗しました');
      }
    } catch (error) {
      toast.error('APIキーの検証中にエラーが発生しました');
    } finally {
      setValidatingKeys(prev => ({ ...prev, [provider]: false }));
    }
  }, [settings, updateAPIKeysMutation]);

  // 通知テスト
  const handleTestNotification = useCallback(async (type: keyof NotificationSettings) => {
    if (!settings?.notifications[type].enabled) {
      toast.error('通知が無効になっています');
      return;
    }

    setTestingNotifications(prev => ({ ...prev, [type]: true }));
    try {
      const result = await SettingsService.testNotification(type, settings.notifications[type]);
      if (result.success) {
        toast.success('テスト通知を送信しました');
      } else {
        toast.error(result.error || 'テスト通知の送信に失敗しました');
      }
    } catch (error) {
      toast.error('テスト通知の送信中にエラーが発生しました');
    } finally {
      setTestingNotifications(prev => ({ ...prev, [type]: false }));
    }
  }, [settings]);

  // 設定のエクスポート
  const handleExportSettings = useCallback(async () => {
    try {
      const settingsJson = await SettingsService.exportSettings();
      const blob = new Blob([settingsJson], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `abds-settings-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('設定をエクスポートしました');
    } catch (error) {
      toast.error('エクスポートに失敗しました');
    }
  }, []);

  // 設定のインポート
  const handleImportSettings = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const settingsJson = e.target?.result as string;
        const result = await SettingsService.importSettings(settingsJson);

        if (result.success) {
          toast.success('設定をインポートしました');
          queryClient.invalidateQueries({ queryKey: ['settings'] });
        } else {
          toast.error(result.error || 'インポートに失敗しました');
        }
      } catch (error) {
        toast.error('ファイルの読み込みに失敗しました');
      }
    };
    reader.readAsText(file);

    // ファイル入力をリセット
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [queryClient]);

  // 設定のリセット
  const handleResetSettings = useCallback(async () => {
    if (window.confirm('すべての設定をデフォルトにリセットしますか？この操作は元に戻せません。')) {
      try {
        await SettingsService.resetToDefaults();
        toast.success('設定をデフォルトにリセットしました');
        queryClient.invalidateQueries({ queryKey: ['settings'] });
      } catch (error) {
        toast.error('リセットに失敗しました');
      }
    }
  }, [queryClient]);

  // タブ設定
  const tabs = [
    { id: 'whitelist', label: 'ホワイトリスト', icon: Globe },
    { id: 'thresholds', label: 'しきい値', icon: Shield },
    { id: 'notifications', label: '通知', icon: Bell },
    { id: 'apikeys', label: 'APIキー', icon: Key },
    { id: 'system', label: 'システム', icon: Server },
  ] as const;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">設定を読み込み中...</span>
      </div>
    );
  }

  if (error || !settings) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200 text-center max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            設定の読み込みに失敗しました
          </h2>
          <button onClick={() => refetch()} className="btn-primary">
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <SettingsIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">設定</h1>
                <p className="text-sm text-gray-600 mt-1">
                  システムの動作を設定します
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleExportSettings}
                className="btn-outline text-sm"
                title="設定をエクスポート"
              >
                <Download className="w-4 h-4 mr-2" />
                エクスポート
              </button>

              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-outline text-sm"
                title="設定をインポート"
              >
                <Upload className="w-4 h-4 mr-2" />
                インポート
              </button>

              <button
                onClick={handleResetSettings}
                className="btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50"
                title="設定をリセット"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                リセット
              </button>
            </div>
          </div>

          {/* タブナビゲーション */}
          <div className="mt-6">
            <nav className="flex space-x-8">
              {tabs.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
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
        {/* ホワイトリスト管理 */}
        {activeTab === 'whitelist' && (
          <WhitelistManager />
        )}

        {/* しきい値設定 */}
        {activeTab === 'thresholds' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">しきい値設定</h2>
                <p className="text-sm text-gray-600 mt-1">
                  脅威検出のしきい値を設定します
                </p>
              </div>
              <button
                onClick={() => handleSaveThresholds(settings.thresholds)}
                disabled={updateThresholdsMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                {updateThresholdsMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </>
                )}
              </button>
            </div>

            <ThresholdSettingsForm
              thresholds={settings.thresholds}
              onChange={(thresholds) => {
                // 状態を更新する関数が必要
              }}
            />
          </div>
        )}

        {/* 通知設定 */}
        {activeTab === 'notifications' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">通知設定</h2>
                <p className="text-sm text-gray-600 mt-1">
                  アラート通知の設定を管理します
                </p>
              </div>
              <button
                onClick={() => handleSaveNotifications(settings.notifications)}
                disabled={updateNotificationsMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                {updateNotificationsMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </>
                )}
              </button>
            </div>

            <NotificationSettingsForm
              notifications={settings.notifications}
              onTest={handleTestNotification}
              testingStates={testingNotifications}
            />
          </div>
        )}

        {/* APIキー管理 */}
        {activeTab === 'apikeys' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">APIキー管理</h2>
                <p className="text-sm text-gray-600 mt-1">
                  外部サービスのAPIキーを管理します
                </p>
              </div>
              <button
                onClick={() => updateAPIKeysMutation.mutate(settings.apiKeys)}
                disabled={updateAPIKeysMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                {updateAPIKeysMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </>
                )}
              </button>
            </div>

            <APIKeySettingsForm
              apiKeys={settings.apiKeys}
              showKeys={showAPIKeys}
              validatingStates={validatingKeys}
              onToggleVisibility={(provider) =>
                setShowAPIKeys(prev => ({ ...prev, [provider]: !prev[provider] }))
              }
              onValidate={handleValidateAPIKey}
            />
          </div>
        )}

        {/* システム設定 */}
        {activeTab === 'system' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">システム設定</h2>
                <p className="text-sm text-gray-600 mt-1">
                  システム全体の動作設定を管理します
                </p>
              </div>
              <button
                onClick={() => updateSystemMutation.mutate(settings.system)}
                disabled={updateSystemMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                {updateSystemMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </>
                )}
              </button>
            </div>

            <SystemSettingsForm
              system={settings.system}
            />
          </div>
        )}
      </div>

      {/* 隠しファイル入力 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleImportSettings}
        className="hidden"
      />
    </div>
  );
};

// しきい値設定フォーム
const ThresholdSettingsForm: React.FC<{
  thresholds: ThresholdSettings;
  onChange: (thresholds: ThresholdSettings) => void;
}> = ({ thresholds }) => {
  return (
    <div className="space-y-6">
      {/* 脅威スコア */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">脅威スコア</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="label">安全 (0-{thresholds.threatScore.safe})</label>
            <input
              type="number"
              min="0"
              max="100"
              value={thresholds.threatScore.safe}
              className="input"
            />
          </div>
          <div>
            <label className="label">低リスク ({thresholds.threatScore.safe}-{thresholds.threatScore.low})</label>
            <input
              type="number"
              min="0"
              max="100"
              value={thresholds.threatScore.low}
              className="input"
            />
          </div>
          <div>
            <label className="label">中リスク ({thresholds.threatScore.low}-{thresholds.threatScore.medium})</label>
            <input
              type="number"
              min="0"
              max="100"
              value={thresholds.threatScore.medium}
              className="input"
            />
          </div>
          <div>
            <label className="label">高リスク ({thresholds.threatScore.medium}-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={thresholds.threatScore.high}
              className="input"
            />
          </div>
        </div>
      </div>

      {/* その他のしきい値設定... */}
      <div className="text-sm text-gray-500">
        その他のしきい値設定項目は実装を続行してください...
      </div>
    </div>
  );
};

// 通知設定フォーム
const NotificationSettingsForm: React.FC<{
  notifications: NotificationSettings;
  onTest: (type: keyof NotificationSettings) => void;
  testingStates: Record<string, boolean>;
}> = ({ notifications, onTest, testingStates }) => {
  return (
    <div className="space-y-6">
      {/* メール通知 */}
      <div className="p-4 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={notifications.email.enabled}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <h3 className="text-sm font-semibold text-gray-900">メール通知</h3>
          </div>
          <button
            onClick={() => onTest('email')}
            disabled={!notifications.email.enabled || testingStates.email}
            className="btn-outline text-xs disabled:opacity-50"
          >
            {testingStates.email ? (
              <>
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-1"></div>
                テスト中...
              </>
            ) : (
              <>
                <TestTube className="w-3 h-3 mr-1" />
                テスト
              </>
            )}
          </button>
        </div>

        {notifications.email.enabled && (
          <div className="space-y-3">
            <div>
              <label className="label">メールアドレス</label>
              <input
                type="email"
                value={notifications.email.address}
                placeholder="admin@example.com"
                className="input"
              />
            </div>
            <div>
              <label className="label">頻度</label>
              <select value={notifications.email.frequency} className="input">
                <option value="immediate">即座</option>
                <option value="hourly">1時間ごと</option>
                <option value="daily">1日1回</option>
                <option value="weekly">1週間に1回</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* その他の通知設定... */}
      <div className="text-sm text-gray-500">
        その他の通知設定項目は実装を続行してください...
      </div>
    </div>
  );
};

// APIキー設定フォーム
const APIKeySettingsForm: React.FC<{
  apiKeys: APIKeySettings;
  showKeys: Record<string, boolean>;
  validatingStates: Record<string, boolean>;
  onToggleVisibility: (provider: string) => void;
  onValidate: (provider: keyof APIKeySettings, key: string) => void;
}> = ({ apiKeys, showKeys, validatingStates, onToggleVisibility, onValidate }) => {
  const providers = [
    { key: 'gemini', label: 'Google Gemini', description: 'AI画像分析用' },
    { key: 'openai', label: 'OpenAI', description: 'GPT分析用' },
    { key: 'serpapi', label: 'SerpAPI', description: '画像検索用' },
    { key: 'googleCustomSearch', label: 'Google Custom Search', description: 'カスタム検索用' },
  ] as const;

  return (
    <div className="space-y-4">
      {providers.map(({ key, label, description }) => {
        const keyData = apiKeys[key];
        const isShown = showKeys[key];
        const isValidating = validatingStates[key];

        return (
          <div key={key} className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-gray-900">{label}</h3>
                <p className="text-xs text-gray-600">{description}</p>
              </div>
              {keyData.isValid && (
                <div className="flex items-center space-x-1 text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-xs">検証済み</span>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex space-x-2">
                <div className="flex-1 relative">
                  <input
                    type={isShown ? 'text' : 'password'}
                    value={isShown ? keyData.key : maskAPIKey(keyData.key)}
                    placeholder="APIキーを入力..."
                    className="input pr-10"
                    readOnly={!isShown}
                  />
                  <button
                    onClick={() => onToggleVisibility(key)}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {isShown ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  onClick={() => onValidate(key, keyData.key)}
                  disabled={!keyData.key || isValidating}
                  className="btn-outline disabled:opacity-50"
                >
                  {isValidating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      検証中...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      検証
                    </>
                  )}
                </button>
              </div>

              {keyData.usage && (
                <div className="text-xs text-gray-600">
                  使用量: 日次 {keyData.usage.daily} / 月次 {keyData.usage.monthly} (上限: {keyData.usage.limit})
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// システム設定フォーム
const SystemSettingsForm: React.FC<{
  system: SystemSettings;
}> = ({ system }) => {
  return (
    <div className="space-y-6">
      {/* 一般設定 */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">一般設定</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">言語</label>
            <select value={system.general.language} className="input">
              <option value="ja">日本語</option>
              <option value="en">English</option>
            </select>
          </div>
          <div>
            <label className="label">タイムゾーン</label>
            <select value={system.general.timezone} className="input">
              <option value="Asia/Tokyo">Asia/Tokyo</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>
      </div>

      {/* その他のシステム設定... */}
      <div className="text-sm text-gray-500">
        その他のシステム設定項目は実装を続行してください...
      </div>
    </div>
  );
};

export default Settings;