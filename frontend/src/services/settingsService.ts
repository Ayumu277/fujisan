import { api } from './api';

// 設定データの型定義
export interface ThresholdSettings {
  threatScore: {
    safe: number;
    low: number;
    medium: number;
    high: number;
  };
  similarityScore: {
    minimum: number;
    high: number;
  };
  confidenceScore: {
    minimum: number;
    reliable: number;
  };
  domainTrust: {
    minimum: number;
    trusted: number;
  };
  aiAnalysis: {
    contentAbuse: number;
    copyrightInfringement: number;
    commercialUseThreshold: number;
  };
}

export interface NotificationSettings {
  email: {
    enabled: boolean;
    address: string;
    frequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
    threatLevels: ('HIGH' | 'MEDIUM' | 'LOW')[];
  };
  browser: {
    enabled: boolean;
    threatLevels: ('HIGH' | 'MEDIUM' | 'LOW')[];
  };
  webhook: {
    enabled: boolean;
    url: string;
    secret: string;
    threatLevels: ('HIGH' | 'MEDIUM' | 'LOW')[];
    retryAttempts: number;
  };
  slack: {
    enabled: boolean;
    webhook: string;
    channel: string;
    threatLevels: ('HIGH' | 'MEDIUM' | 'LOW')[];
  };
  teams: {
    enabled: boolean;
    webhook: string;
    threatLevels: ('HIGH' | 'MEDIUM' | 'LOW')[];
  };
}

export interface APIKeySettings {
  gemini: {
    key: string;
    isValid: boolean;
    lastValidated: string;
    usage?: {
      daily: number;
      monthly: number;
      limit: number;
    };
  };
  openai: {
    key: string;
    isValid: boolean;
    lastValidated: string;
    usage?: {
      daily: number;
      monthly: number;
      limit: number;
    };
  };
  serpapi: {
    key: string;
    isValid: boolean;
    lastValidated: string;
    usage?: {
      daily: number;
      monthly: number;
      limit: number;
    };
  };
  googleCustomSearch: {
    apiKey: string;
    searchEngineId: string;
    isValid: boolean;
    lastValidated: string;
    usage?: {
      daily: number;
      monthly: number;
      limit: number;
    };
  };
}

export interface SystemSettings {
  general: {
    language: 'ja' | 'en';
    timezone: string;
    dateFormat: string;
    theme: 'light' | 'dark' | 'auto';
  };
  security: {
    sessionTimeout: number;
    maxLoginAttempts: number;
    passwordMinLength: number;
    requireTwoFactor: boolean;
  };
  performance: {
    maxConcurrentAnalyses: number;
    cacheExpiryHours: number;
    imageSizeLimit: number;
    batchProcessingSize: number;
  };
  storage: {
    retentionDays: number;
    autoCleanup: boolean;
    backupEnabled: boolean;
    backupFrequency: 'daily' | 'weekly' | 'monthly';
  };
}

export interface AllSettings {
  thresholds: ThresholdSettings;
  notifications: NotificationSettings;
  apiKeys: APIKeySettings;
  system: SystemSettings;
  lastUpdated: string;
  updatedBy: string;
}

// デフォルト設定
const defaultSettings: AllSettings = {
  thresholds: {
    threatScore: {
      safe: 20,
      low: 40,
      medium: 70,
      high: 85,
    },
    similarityScore: {
      minimum: 60,
      high: 85,
    },
    confidenceScore: {
      minimum: 50,
      reliable: 80,
    },
    domainTrust: {
      minimum: 30,
      trusted: 80,
    },
    aiAnalysis: {
      contentAbuse: 70,
      copyrightInfringement: 75,
      commercialUseThreshold: 80,
    },
  },
  notifications: {
    email: {
      enabled: true,
      address: '',
      frequency: 'daily',
      threatLevels: ['HIGH', 'MEDIUM'],
    },
    browser: {
      enabled: true,
      threatLevels: ['HIGH'],
    },
    webhook: {
      enabled: false,
      url: '',
      secret: '',
      threatLevels: ['HIGH', 'MEDIUM'],
      retryAttempts: 3,
    },
    slack: {
      enabled: false,
      webhook: '',
      channel: '#security',
      threatLevels: ['HIGH'],
    },
    teams: {
      enabled: false,
      webhook: '',
      threatLevels: ['HIGH'],
    },
  },
  apiKeys: {
    gemini: {
      key: '',
      isValid: false,
      lastValidated: '',
    },
    openai: {
      key: '',
      isValid: false,
      lastValidated: '',
    },
    serpapi: {
      key: '',
      isValid: false,
      lastValidated: '',
    },
    googleCustomSearch: {
      apiKey: '',
      searchEngineId: '',
      isValid: false,
      lastValidated: '',
    },
  },
  system: {
    general: {
      language: 'ja',
      timezone: 'Asia/Tokyo',
      dateFormat: 'yyyy/MM/dd',
      theme: 'light',
    },
    security: {
      sessionTimeout: 480,
      maxLoginAttempts: 5,
      passwordMinLength: 8,
      requireTwoFactor: false,
    },
    performance: {
      maxConcurrentAnalyses: 5,
      cacheExpiryHours: 24,
      imageSizeLimit: 10485760, // 10MB
      batchProcessingSize: 10,
    },
    storage: {
      retentionDays: 90,
      autoCleanup: true,
      backupEnabled: false,
      backupFrequency: 'weekly',
    },
  },
  lastUpdated: new Date().toISOString(),
  updatedBy: 'system',
};

// モック API 関数
const mockSettingsAPI = {
  // 全設定を取得
  getAllSettings: async (): Promise<AllSettings> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const storedSettings = localStorage.getItem('app-settings');
    if (storedSettings) {
      return { ...defaultSettings, ...JSON.parse(storedSettings) };
    }
    return defaultSettings;
  },

  // しきい値設定を更新
  updateThresholds: async (thresholds: ThresholdSettings): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const settings = await mockSettingsAPI.getAllSettings();
    const updatedSettings = {
      ...settings,
      thresholds,
      lastUpdated: new Date().toISOString(),
      updatedBy: 'Current User',
    };
    localStorage.setItem('app-settings', JSON.stringify(updatedSettings));
  },

  // 通知設定を更新
  updateNotifications: async (notifications: NotificationSettings): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const settings = await mockSettingsAPI.getAllSettings();
    const updatedSettings = {
      ...settings,
      notifications,
      lastUpdated: new Date().toISOString(),
      updatedBy: 'Current User',
    };
    localStorage.setItem('app-settings', JSON.stringify(updatedSettings));
  },

  // APIキー設定を更新
  updateAPIKeys: async (apiKeys: APIKeySettings): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const settings = await mockSettingsAPI.getAllSettings();
    const updatedSettings = {
      ...settings,
      apiKeys,
      lastUpdated: new Date().toISOString(),
      updatedBy: 'Current User',
    };
    localStorage.setItem('app-settings', JSON.stringify(updatedSettings));
  },

  // システム設定を更新
  updateSystemSettings: async (system: SystemSettings): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const settings = await mockSettingsAPI.getAllSettings();
    const updatedSettings = {
      ...settings,
      system,
      lastUpdated: new Date().toISOString(),
      updatedBy: 'Current User',
    };
    localStorage.setItem('app-settings', JSON.stringify(updatedSettings));
  },

  // APIキーの検証
  validateAPIKey: async (provider: keyof APIKeySettings, key: string): Promise<{
    isValid: boolean;
    error?: string;
    usage?: any;
  }> => {
    await new Promise(resolve => setTimeout(resolve, 1000));

    // モック検証ロジック
    if (!key || key.length < 10) {
      return { isValid: false, error: 'APIキーが短すぎます' };
    }

    if (key.includes('invalid')) {
      return { isValid: false, error: '無効なAPIキーです' };
    }

    // モック使用量データ
    const mockUsage = {
      daily: Math.floor(Math.random() * 1000),
      monthly: Math.floor(Math.random() * 10000),
      limit: provider === 'gemini' ? 1000000 : provider === 'serpapi' ? 100 : 1000,
    };

    return {
      isValid: true,
      usage: mockUsage,
    };
  },

  // 通知テスト送信
  testNotification: async (type: keyof NotificationSettings, settings: any): Promise<{
    success: boolean;
    error?: string;
  }> => {
    await new Promise(resolve => setTimeout(resolve, 1500));

    if (type === 'email' && !settings.address) {
      return { success: false, error: 'メールアドレスが設定されていません' };
    }

    if (type === 'webhook' && !settings.url) {
      return { success: false, error: 'WebhookのURLが設定されていません' };
    }

    // ランダムで失敗をシミュレート
    if (Math.random() < 0.1) {
      return { success: false, error: 'テスト送信に失敗しました' };
    }

    return { success: true };
  },

  // 設定をデフォルトにリセット
  resetToDefaults: async (): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    localStorage.removeItem('app-settings');
  },

  // 設定のエクスポート
  exportSettings: async (): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    const settings = await mockSettingsAPI.getAllSettings();
    return JSON.stringify(settings, null, 2);
  },

  // 設定のインポート
  importSettings: async (settingsJson: string): Promise<{
    success: boolean;
    error?: string;
    imported?: Partial<AllSettings>;
  }> => {
    await new Promise(resolve => setTimeout(resolve, 500));

    try {
      const imported = JSON.parse(settingsJson);

      // 基本的な構造検証
      if (!imported || typeof imported !== 'object') {
        return { success: false, error: '無効な設定ファイルです' };
      }

      // 現在の設定とマージ
      const currentSettings = await mockSettingsAPI.getAllSettings();
      const mergedSettings = {
        ...currentSettings,
        ...imported,
        lastUpdated: new Date().toISOString(),
        updatedBy: 'Import',
      };

      localStorage.setItem('app-settings', JSON.stringify(mergedSettings));

      return { success: true, imported };
    } catch (error) {
      return { success: false, error: 'ファイルの解析に失敗しました' };
    }
  },

  // 設定履歴の取得
  getSettingsHistory: async (): Promise<Array<{
    id: string;
    timestamp: string;
    user: string;
    section: string;
    changes: Record<string, any>;
  }>> => {
    await new Promise(resolve => setTimeout(resolve, 500));

    // モック履歴データ
    return [
      {
        id: 'hist-1',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        user: '管理者',
        section: 'しきい値設定',
        changes: { 'threatScore.high': { from: 80, to: 85 } },
      },
      {
        id: 'hist-2',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        user: 'セキュリティチーム',
        section: '通知設定',
        changes: { 'email.frequency': { from: 'immediate', to: 'daily' } },
      },
      {
        id: 'hist-3',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        user: '管理者',
        section: 'APIキー',
        changes: { 'gemini.key': { from: '***masked***', to: '***masked***' } },
      },
    ];
  },
};

// エクスポート用の関数
export const getAllSettings = () => mockSettingsAPI.getAllSettings();
export const updateThresholds = (thresholds: ThresholdSettings) => mockSettingsAPI.updateThresholds(thresholds);
export const updateNotifications = (notifications: NotificationSettings) => mockSettingsAPI.updateNotifications(notifications);
export const updateAPIKeys = (apiKeys: APIKeySettings) => mockSettingsAPI.updateAPIKeys(apiKeys);
export const updateSystemSettings = (system: SystemSettings) => mockSettingsAPI.updateSystemSettings(system);
export const validateAPIKey = (provider: keyof APIKeySettings, key: string) => mockSettingsAPI.validateAPIKey(provider, key);
export const testNotification = (type: keyof NotificationSettings, settings: any) => mockSettingsAPI.testNotification(type, settings);
export const resetToDefaults = () => mockSettingsAPI.resetToDefaults();
export const exportSettings = () => mockSettingsAPI.exportSettings();
export const importSettings = (settingsJson: string) => mockSettingsAPI.importSettings(settingsJson);
export const getSettingsHistory = () => mockSettingsAPI.getSettingsHistory();

// ユーティリティ関数
export const maskAPIKey = (key: string): string => {
  if (!key) return '';
  if (key.length <= 8) return '●'.repeat(key.length);
  return key.slice(0, 4) + '●'.repeat(key.length - 8) + key.slice(-4);
};

export const validateThresholds = (thresholds: ThresholdSettings): string[] => {
  const errors: string[] = [];

  // 脅威スコアの順序チェック
  const { safe, low, medium, high } = thresholds.threatScore;
  if (safe >= low) errors.push('安全スコアは低リスクスコアより小さい必要があります');
  if (low >= medium) errors.push('低リスクスコアは中リスクスコアより小さい必要があります');
  if (medium >= high) errors.push('中リスクスコアは高リスクスコアより小さい必要があります');

  // 範囲チェック
  const allScores = [safe, low, medium, high,
                    thresholds.similarityScore.minimum, thresholds.similarityScore.high,
                    thresholds.confidenceScore.minimum, thresholds.confidenceScore.reliable,
                    thresholds.domainTrust.minimum, thresholds.domainTrust.trusted];

  if (allScores.some(score => score < 0 || score > 100)) {
    errors.push('すべてのスコアは0-100の範囲内である必要があります');
  }

  return errors;
};

export const validateNotificationSettings = (notifications: NotificationSettings): string[] => {
  const errors: string[] = [];

  if (notifications.email.enabled && !notifications.email.address) {
    errors.push('メール通知が有効な場合、メールアドレスは必須です');
  }

  if (notifications.webhook.enabled && !notifications.webhook.url) {
    errors.push('Webhook通知が有効な場合、URLは必須です');
  }

  if (notifications.slack.enabled && !notifications.slack.webhook) {
    errors.push('Slack通知が有効な場合、Webhook URLは必須です');
  }

  if (notifications.teams.enabled && !notifications.teams.webhook) {
    errors.push('Teams通知が有効な場合、Webhook URLは必須です');
  }

  return errors;
};

export const SettingsService = {
  getAllSettings: mockSettingsAPI.getAllSettings,
  updateThresholds: mockSettingsAPI.updateThresholds,
  updateNotifications: mockSettingsAPI.updateNotifications,
  updateAPIKeys: mockSettingsAPI.updateAPIKeys,
  updateSystemSettings: mockSettingsAPI.updateSystemSettings,
  validateAPIKey: mockSettingsAPI.validateAPIKey,
  testNotification: mockSettingsAPI.testNotification,
  resetToDefaults: mockSettingsAPI.resetToDefaults,
  exportSettings: mockSettingsAPI.exportSettings,
  importSettings: mockSettingsAPI.importSettings,
  getSettingsHistory: mockSettingsAPI.getSettingsHistory,
};