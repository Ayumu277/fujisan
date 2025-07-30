// 共通の型定義

// ID型
export type ID = string | number;

// 基本エンティティ
export interface BaseEntity {
  id: ID;
  createdAt: string;
  updatedAt: string;
}

// ページネーション
export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// ソート設定
export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

// フィルター設定
export interface FilterConfig {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in';
  value: any;
}

// 検索クエリ
export interface SearchQuery extends PaginationParams {
  q?: string;
  filters?: FilterConfig[];
}

// ファイル情報
export interface FileInfo {
  name: string;
  size: number;
  type: string;
  url?: string;
}

// 選択肢項目
export interface SelectOption {
  label: string;
  value: string | number;
  disabled?: boolean;
}

// フォーム状態
export interface FormState {
  isLoading: boolean;
  isSubmitting: boolean;
  errors: Record<string, string[]>;
  touched: Record<string, boolean>;
}

// 通知タイプ
export type NotificationType = 'success' | 'error' | 'warning' | 'info';

// 通知メッセージ
export interface NotificationMessage {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
}