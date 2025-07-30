import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import toast from 'react-hot-toast';

// ヘルスチェック用フック
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/health'),
    refetchInterval: 30000, // 30秒ごとに再取得
  });
};

// アプリ情報取得用フック
export const useAppInfo = () => {
  return useQuery({
    queryKey: ['app-info'],
    queryFn: () => api.get('/info'),
    staleTime: 10 * 60 * 1000, // 10分間キャッシュ
  });
};

// 汎用的なAPIフック
export const useApiQuery = <T = any>(
  queryKey: string[],
  url: string,
  options?: any
) => {
  return useQuery({
    queryKey,
    queryFn: () => api.get<T>(url),
    ...options,
  });
};

// 汎用的な変更フック
export const useApiMutation = <T = any, K = any>(
  mutationFn: (data: K) => Promise<T>,
  options?: {
    onSuccess?: (data: T) => void;
    onError?: (error: any) => void;
    invalidateQueries?: string[][];
  }
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      options?.onSuccess?.(data);
      // 関連するクエリを無効化
      options?.invalidateQueries?.forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
    },
    onError: (error) => {
      console.error('Mutation error:', error);
      options?.onError?.(error);
    },
  });
};

export default useApiQuery;