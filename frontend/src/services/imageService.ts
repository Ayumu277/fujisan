import axios, { AxiosProgressEvent } from 'axios';
import { api } from './api';

// TypeScript型定義
export interface ImageUploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface ImageUploadResponse {
  id: string;
  filename: string;
  originalName: string;
  size: number;
  mimeType: string;
  uploadPath: string;
  thumbnailPath?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
}

export interface ImageUploadError {
  code: string;
  message: string;
  details?: any;
}

export interface ImageFile {
  file: File;
  id: string;
  preview: string;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  progress: number;
  response?: ImageUploadResponse;
  error?: ImageUploadError;
}

// ファイル検証設定
const UPLOAD_CONFIG = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  maxFiles: 10,
};

// ファイル検証
export const validateImageFile = (file: File): string | null => {
  // ファイルサイズチェック
  if (file.size > UPLOAD_CONFIG.maxFileSize) {
    return `ファイルサイズが大きすぎます。最大${UPLOAD_CONFIG.maxFileSize / 1024 / 1024}MBまでです。`;
  }

  // ファイルタイプチェック
  if (!UPLOAD_CONFIG.allowedTypes.includes(file.type)) {
    return '対応していないファイル形式です。JPEG、PNG、GIF、WebPのみサポートしています。';
  }

  return null;
};

// 画像プレビューURL生成
export const createImagePreview = (file: File): string => {
  return URL.createObjectURL(file);
};

// プレビューURLクリーンアップ
export const revokeImagePreview = (preview: string): void => {
  URL.revokeObjectURL(preview);
};

// 単一ファイルアップロード
export const uploadImage = async (
  file: File,
  onProgress?: (progress: ImageUploadProgress) => void
): Promise<ImageUploadResponse> => {
  // ファイル検証
  const validationError = validateImageFile(file);
  if (validationError) {
    throw new Error(validationError);
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post<ImageUploadResponse>(
      'http://localhost:8000/api/v1/images/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress: ImageUploadProgress = {
              loaded: progressEvent.loaded,
              total: progressEvent.total,
              percentage: Math.round((progressEvent.loaded * 100) / progressEvent.total),
            };
            onProgress(progress);
          }
        },
        timeout: 30000, // 30秒タイムアウト
      }
    );

    return response.data;
  } catch (error: any) {
    // エラーハンドリング
    if (error.response) {
      // サーバーエラー
      const errorData = error.response.data;
      throw new Error(errorData.message || 'アップロードに失敗しました');
    } else if (error.request) {
      // ネットワークエラー
      throw new Error('ネットワークエラーが発生しました');
    } else {
      // その他のエラー
      throw new Error(error.message || '不明なエラーが発生しました');
    }
  }
};

// 複数ファイル並行アップロード
export const uploadMultipleImages = async (
  files: File[],
  onProgress?: (fileId: string, progress: ImageUploadProgress) => void,
  onComplete?: (fileId: string, response: ImageUploadResponse) => void,
  onError?: (fileId: string, error: Error) => void
): Promise<ImageUploadResponse[]> => {
  const uploadPromises = files.map(async (file, index) => {
    const fileId = `file-${index}-${Date.now()}`;

    try {
      const response = await uploadImage(file, (progress) => {
        onProgress?.(fileId, progress);
      });

      onComplete?.(fileId, response);
      return response;
    } catch (error) {
      onError?.(fileId, error as Error);
      throw error;
    }
  });

  try {
    const results = await Promise.allSettled(uploadPromises);
    const successfulUploads = results
      .filter((result): result is PromiseFulfilledResult<ImageUploadResponse> =>
        result.status === 'fulfilled'
      )
      .map(result => result.value);

    return successfulUploads;
  } catch (error) {
    throw new Error('一部またはすべてのファイルのアップロードに失敗しました');
  }
};

// アップロード済み画像取得
export const getUploadedImages = async (
  page: number = 1,
  limit: number = 20
): Promise<{ images: ImageUploadResponse[]; total: number; hasMore: boolean }> => {
  try {
    const response = await api.get(`/api/v1/images?page=${page}&limit=${limit}`);
    return {
      images: response.images || [],
      total: response.total || 0,
      hasMore: response.hasMore || false,
    };
  } catch (error) {
    console.error('Failed to fetch uploaded images:', error);
    return { images: [], total: 0, hasMore: false };
  }
};

// 画像削除
export const deleteImage = async (imageId: string): Promise<void> => {
  try {
    await api.delete(`/api/v1/images/${imageId}`);
  } catch (error) {
    throw new Error('画像の削除に失敗しました');
  }
};

// 画像検索開始
export const startImageSearch = async (imageId: string): Promise<{ searchId: string }> => {
  try {
    const response = await api.post(`/api/v1/search/start/${imageId}`);
    return response;
  } catch (error) {
    throw new Error('画像検索の開始に失敗しました');
  }
};

// ユーティリティ関数
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileExtension = (filename: string): string => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
};

export const isImageFile = (file: File): boolean => {
  return UPLOAD_CONFIG.allowedTypes.includes(file.type);
};

export { UPLOAD_CONFIG };