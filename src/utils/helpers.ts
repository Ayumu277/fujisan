// ヘルパー関数

/**
 * 遅延処理
 */
export const delay = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * 値がnullまたはundefinedかチェック
 */
export const isNullOrUndefined = (value: any): value is null | undefined =>
  value === null || value === undefined;

/**
 * 空の値かチェック（null, undefined, 空文字, 空配列, 空オブジェクト）
 */
export const isEmpty = (value: any): boolean => {
  if (isNullOrUndefined(value)) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

/**
 * 配列をチャンク（指定サイズで分割）
 */
export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

/**
 * オブジェクトから指定キーのみ抽出
 */
export const pick = <T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

/**
 * オブジェクトから指定キーを除外
 */
export const omit = <T, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => {
    delete result[key];
  });
  return result;
};

/**
 * 配列内の重複を削除
 */
export const unique = <T>(array: T[]): T[] => [...new Set(array)];

/**
 * 深いオブジェクトのクローン
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const copy = {} as { [K in keyof T]: T[K] };
    Object.keys(obj).forEach(key => {
      copy[key as keyof T] = deepClone((obj as any)[key]);
    });
    return copy;
  }
  return obj;
};

/**
 * URLからファイル名を抽出
 */
export const getFileNameFromUrl = (url: string): string => {
  try {
    const pathname = new URL(url).pathname;
    return pathname.split('/').pop() || '';
  } catch {
    return '';
  }
};

/**
 * ランダムなIDを生成
 */
export const generateId = (prefix = 'id'): string =>
  `${prefix}_${Math.random().toString(36).substr(2, 9)}`;

/**
 * 数値を3桁区切りでフォーマット
 */
export const formatNumber = (num: number): string =>
  num.toLocaleString('ja-JP');

/**
 * バイト数を人間が読みやすい形式に変換
 */
export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};