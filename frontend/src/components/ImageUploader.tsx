import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  X,
  Image as ImageIcon,
  AlertCircle,
  CheckCircle,
  Loader2,
  Eye,
  Trash2,
  Search,
} from 'lucide-react';
import toast from 'react-hot-toast';

import {
  ImageFile,
  uploadImage,
  validateImageFile,
  createImagePreview,
  revokeImagePreview,
  formatFileSize,
  startImageSearch,
  UPLOAD_CONFIG,
} from '../services/imageService';

interface ImageUploaderProps {
  onFilesUploaded?: (files: ImageFile[]) => void;
  onUploadComplete?: (uploadedFiles: ImageFile[]) => void;
  maxFiles?: number;
  disabled?: boolean;
  className?: string;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onFilesUploaded,
  onUploadComplete,
  maxFiles = UPLOAD_CONFIG.maxFiles,
  disabled = false,
  className = '',
}) => {
  const [files, setFiles] = useState<ImageFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // ファイルドロップ処理
  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // 拒否されたファイルの処理
    rejectedFiles.forEach(({ file, errors }) => {
      errors.forEach((error: any) => {
        let message = 'ファイルが拒否されました';
        switch (error.code) {
          case 'file-too-large':
            message = `ファイルサイズが大きすぎます: ${file.name}`;
            break;
          case 'file-invalid-type':
            message = `対応していないファイル形式です: ${file.name}`;
            break;
          case 'too-many-files':
            message = `ファイル数が上限を超えています（最大${maxFiles}個）`;
            break;
          default:
            message = `ファイルエラー: ${error.message}`;
        }
        toast.error(message);
      });
    });

    // 受け入れられたファイルの処理
    const newImageFiles: ImageFile[] = acceptedFiles.map((file, index) => {
      const validationError = validateImageFile(file);
      const preview = createImagePreview(file);

      return {
        file,
        id: `${Date.now()}-${index}`,
        preview,
        status: validationError ? 'failed' : 'pending',
        progress: 0,
        error: validationError ? { code: 'validation', message: validationError } : undefined,
      };
    });

    setFiles(prev => {
      const combined = [...prev, ...newImageFiles];
      // 最大ファイル数制限
      if (combined.length > maxFiles) {
        toast.error(`最大${maxFiles}個のファイルまでアップロードできます`);
        return combined.slice(0, maxFiles);
      }
      return combined;
    });

    onFilesUploaded?.(newImageFiles);
  }, [maxFiles, onFilesUploaded]);

  // Dropzone設定
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp'],
    },
    maxSize: UPLOAD_CONFIG.maxFileSize,
    maxFiles,
    disabled: disabled || isUploading,
    multiple: true,
  });

  // ファイル削除
  const removeFile = useCallback((fileId: string) => {
    setFiles(prev => {
      const fileToRemove = prev.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        revokeImagePreview(fileToRemove.preview);
      }
      return prev.filter(f => f.id !== fileId);
    });
  }, []);

  // 全ファイル削除
  const clearAllFiles = useCallback(() => {
    files.forEach(file => {
      if (file.preview) {
        revokeImagePreview(file.preview);
      }
    });
    setFiles([]);
  }, [files]);

  // ファイルアップロード実行
  const uploadFiles = useCallback(async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) {
      toast.error('アップロードするファイルがありません');
      return;
    }

    setIsUploading(true);

    try {
      // 各ファイルを並行アップロード
      const uploadPromises = pendingFiles.map(async (imageFile) => {
        // ステータスを更新
        setFiles(prev => prev.map(f =>
          f.id === imageFile.id ? { ...f, status: 'uploading' as const } : f
        ));

        try {
          const response = await uploadImage(imageFile.file, (progress) => {
            // 進捗更新
            setFiles(prev => prev.map(f =>
              f.id === imageFile.id ? { ...f, progress: progress.percentage } : f
            ));
          });

          // 成功時の処理
          setFiles(prev => prev.map(f =>
            f.id === imageFile.id
              ? { ...f, status: 'completed' as const, response, progress: 100 }
              : f
          ));

          return { ...imageFile, response, status: 'completed' as const };
        } catch (error) {
          // エラー時の処理
          const errorMessage = error instanceof Error ? error.message : 'アップロードに失敗しました';

          setFiles(prev => prev.map(f =>
            f.id === imageFile.id
              ? {
                  ...f,
                  status: 'failed' as const,
                  error: { code: 'upload', message: errorMessage },
                  progress: 0
                }
              : f
          ));

          toast.error(`${imageFile.file.name}: ${errorMessage}`);
          throw error;
        }
      });

      const results = await Promise.allSettled(uploadPromises);
      const successful = results
        .filter((result): result is PromiseFulfilledResult<ImageFile> => result.status === 'fulfilled')
        .map(result => result.value);

      if (successful.length > 0) {
        toast.success(`${successful.length}個のファイルのアップロードが完了しました`);
        onUploadComplete?.(successful);
      }

    } catch (error) {
      console.error('Upload process failed:', error);
    } finally {
      setIsUploading(false);
    }
  }, [files, onUploadComplete]);

  // 画像検索開始
  const handleSearchImage = useCallback(async (imageFile: ImageFile) => {
    if (!imageFile.response?.id) {
      toast.error('アップロード完了後に検索できます');
      return;
    }

    try {
      const { searchId } = await startImageSearch(imageFile.response.id);
      toast.success('画像検索を開始しました');
      // 検索ページに遷移するなどの処理をここに追加
    } catch (error) {
      toast.error('画像検索の開始に失敗しました');
    }
  }, []);

  // コンポーネントアンマウント時のクリーンアップ
  useEffect(() => {
    return () => {
      files.forEach(file => {
        if (file.preview) {
          revokeImagePreview(file.preview);
        }
      });
    };
  }, [files]);

  // アップロード統計
  const completedCount = files.filter(f => f.status === 'completed').length;
  const failedCount = files.filter(f => f.status === 'failed').length;
  const uploadingCount = files.filter(f => f.status === 'uploading').length;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* ドロップゾーン */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
          ${isDragActive
            ? isDragReject
              ? 'border-red-400 bg-red-50'
              : 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${disabled || isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
            <Upload className="w-8 h-8 text-gray-400" />
          </div>

          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive
                ? isDragReject
                  ? 'サポートされていないファイル形式です'
                  : 'ファイルをドロップしてください'
                : 'ファイルをドラッグ&ドロップするか、クリックして選択'
              }
            </p>
            <p className="text-sm text-gray-500 mt-2">
              JPEG、PNG、GIF、WebP形式をサポート（最大{formatFileSize(UPLOAD_CONFIG.maxFileSize)}）
            </p>
            <p className="text-xs text-gray-400 mt-1">
              最大{maxFiles}個のファイルまで同時アップロード可能
            </p>
          </div>
        </div>
      </div>

      {/* ファイル一覧 */}
      {files.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              選択されたファイル ({files.length})
            </h3>
            <div className="flex items-center space-x-3">
              {completedCount > 0 && (
                <span className="text-sm text-green-600">
                  完了: {completedCount}
                </span>
              )}
              {failedCount > 0 && (
                <span className="text-sm text-red-600">
                  失敗: {failedCount}
                </span>
              )}
              <button
                onClick={clearAllFiles}
                className="text-sm text-gray-500 hover:text-red-600 transition-colors"
                disabled={isUploading}
              >
                すべて削除
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {files.map((imageFile) => (
              <FilePreviewCard
                key={imageFile.id}
                imageFile={imageFile}
                onRemove={removeFile}
                onSearch={handleSearchImage}
                disabled={isUploading}
              />
            ))}
          </div>

          {/* アップロードボタン */}
          <div className="flex justify-center pt-4">
            <button
              onClick={uploadFiles}
              disabled={isUploading || files.filter(f => f.status === 'pending').length === 0}
              className="btn-primary px-8 py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  アップロード中... ({uploadingCount}/{files.length})
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  アップロード開始 ({files.filter(f => f.status === 'pending').length}個)
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ファイルプレビューカードコンポーネント
interface FilePreviewCardProps {
  imageFile: ImageFile;
  onRemove: (fileId: string) => void;
  onSearch: (imageFile: ImageFile) => void;
  disabled: boolean;
}

const FilePreviewCard: React.FC<FilePreviewCardProps> = ({
  imageFile,
  onRemove,
  onSearch,
  disabled,
}) => {
  const getStatusIcon = () => {
    switch (imageFile.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'uploading':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <ImageIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (imageFile.status) {
      case 'completed': return 'border-green-200 bg-green-50';
      case 'failed': return 'border-red-200 bg-red-50';
      case 'uploading': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-white';
    }
  };

  return (
    <div className={`rounded-lg border-2 overflow-hidden ${getStatusColor()}`}>
      {/* 画像プレビュー */}
      <div className="aspect-square bg-gray-100 relative">
        <img
          src={imageFile.preview}
          alt={imageFile.file.name}
          className="w-full h-full object-cover"
        />

        {/* ステータスオーバーレイ */}
        <div className="absolute top-2 left-2">
          {getStatusIcon()}
        </div>

        {/* アクションボタン */}
        <div className="absolute top-2 right-2 flex space-x-1">
          {imageFile.status === 'completed' && (
            <button
              onClick={() => onSearch(imageFile)}
              className="p-1.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
              title="画像検索を開始"
            >
              <Search className="w-3 h-3" />
            </button>
          )}
          <button
            onClick={() => onRemove(imageFile.id)}
            disabled={disabled}
            className="p-1.5 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors disabled:opacity-50"
            title="削除"
          >
            <X className="w-3 h-3" />
          </button>
        </div>

        {/* 進捗バー */}
        {imageFile.status === 'uploading' && (
          <div className="absolute bottom-0 left-0 right-0 bg-gray-200 h-2">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${imageFile.progress}%` }}
            />
          </div>
        )}
      </div>

      {/* ファイル情報 */}
      <div className="p-3">
        <p className="text-sm font-medium text-gray-900 truncate" title={imageFile.file.name}>
          {imageFile.file.name}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {formatFileSize(imageFile.file.size)}
        </p>

        {/* エラーメッセージ */}
        {imageFile.error && (
          <p className="text-xs text-red-600 mt-1">
            {imageFile.error.message}
          </p>
        )}

        {/* 進捗テキスト */}
        {imageFile.status === 'uploading' && (
          <p className="text-xs text-blue-600 mt-1">
            {imageFile.progress}% アップロード中...
          </p>
        )}

        {/* 完了情報 */}
        {imageFile.status === 'completed' && imageFile.response && (
          <p className="text-xs text-green-600 mt-1">
            アップロード完了 (ID: {imageFile.response.id.slice(0, 8)}...)
          </p>
        )}
      </div>
    </div>
  );
};

export default ImageUploader;