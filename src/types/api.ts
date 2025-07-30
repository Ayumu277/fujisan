// API レスポンスの基本型
export interface BaseApiResponse {
  status: number;
  message?: string;
}

// ページネーション付きレスポンス
export interface PaginatedResponse<T> extends BaseApiResponse {
  data: T[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// 単一データレスポンス
export interface SingleResponse<T> extends BaseApiResponse {
  data: T;
}

// リストレスポンス
export interface ListResponse<T> extends BaseApiResponse {
  data: T[];
}

// エラーレスポンス
export interface ErrorResponse extends BaseApiResponse {
  error: true;
  details?: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

// ファイルアップロードレスポンス
export interface UploadResponse extends BaseApiResponse {
  data: {
    filename: string;
    originalName: string;
    size: number;
    url: string;
  };
}

// ヘルスチェックレスポンス
export interface HealthResponse extends BaseApiResponse {
  data: {
    status: 'healthy' | 'unhealthy';
    version: string;
    environment: string;
    services: {
      api: string;
      database: string;
      redis: string;
    };
    system: {
      python_version: string;
      fastapi_version: string;
    };
  };
}