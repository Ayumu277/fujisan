import React, { useState, useCallback } from 'react';
import { Upload as UploadIcon, Image, History, Settings, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

import ImageUploader from '../components/ImageUploader';
import { ImageFile, getUploadedImages, deleteImage } from '../services/imageService';

interface UploadPageProps {}

const Upload: React.FC<UploadPageProps> = () => {
  const [uploadedFiles, setUploadedFiles] = useState<ImageFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // アップロード完了時の処理
  const handleUploadComplete = useCallback((files: ImageFile[]) => {
    setUploadedFiles(prev => [...files, ...prev]);
    toast.success(`${files.length}個のファイルのアップロードが完了しました！`);
  }, []);

  // ファイル追加時の処理
  const handleFilesUploaded = useCallback((files: ImageFile[]) => {
    console.log('Files ready for upload:', files);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">画像アップロード</h1>
              <p className="text-gray-600 mt-1">
                不正利用検出システムで分析する画像をアップロードしてください
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="bg-blue-50 rounded-lg px-4 py-2">
                <div className="flex items-center space-x-2 text-blue-700">
                  <Image className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    対応形式: JPEG, PNG, GIF, WebP
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* メインアップロードエリア */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <UploadIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">画像アップロード</h2>
                    <p className="text-sm text-gray-500">
                      複数の画像を同時にアップロードして分析を開始できます
                    </p>
                  </div>
                </div>

                <ImageUploader
                  onFilesUploaded={handleFilesUploaded}
                  onUploadComplete={handleUploadComplete}
                  maxFiles={10}
                  className="mb-6"
                />
              </div>
            </div>

            {/* アップロード手順説明 */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 mt-6">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  アップロード手順
                </h3>
                <div className="space-y-4">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">1</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">画像を選択</h4>
                      <p className="text-sm text-gray-600">
                        上のドロップゾーンに画像ファイルをドラッグ&ドロップするか、クリックしてファイルを選択してください。
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">2</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">プレビュー確認</h4>
                      <p className="text-sm text-gray-600">
                        選択された画像のプレビューが表示されます。不要なファイルは削除ボタンで除外できます。
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">3</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">アップロード実行</h4>
                      <p className="text-sm text-gray-600">
                        「アップロード開始」ボタンをクリックして、ファイルをサーバーにアップロードします。
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">4</span>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">分析開始</h4>
                      <p className="text-sm text-gray-600">
                        アップロード完了後、検索ボタンから画像の不正利用検出分析を開始できます。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* サイドバー */}
          <div className="space-y-6">
            {/* アップロード統計 */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  アップロード状況
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">完了したファイル</span>
                    <span className="text-lg font-semibold text-green-600">
                      {uploadedFiles.filter(f => f.status === 'completed').length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">失敗したファイル</span>
                    <span className="text-lg font-semibold text-red-600">
                      {uploadedFiles.filter(f => f.status === 'failed').length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">処理中のファイル</span>
                    <span className="text-lg font-semibold text-blue-600">
                      {uploadedFiles.filter(f => f.status === 'uploading').length}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 制限事項 */}
            <div className="bg-amber-50 rounded-lg border border-amber-200">
              <div className="p-6">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-amber-800 mb-2">
                      アップロード制限
                    </h3>
                    <ul className="text-sm text-amber-700 space-y-1">
                      <li>• 最大ファイルサイズ: 10MB</li>
                      <li>• 同時アップロード: 10ファイル</li>
                      <li>• 対応形式: JPEG, PNG, GIF, WebP</li>
                      <li>• タイムアウト: 30秒</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* 機能説明 */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  主な機能
                </h3>
                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <div className="p-1 bg-blue-100 rounded">
                      <UploadIcon className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        ドラッグ&ドロップ
                      </h4>
                      <p className="text-xs text-gray-600">
                        簡単操作でファイルアップロード
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="p-1 bg-green-100 rounded">
                      <Image className="w-4 h-4 text-green-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        リアルタイムプレビュー
                      </h4>
                      <p className="text-xs text-gray-600">
                        アップロード前に画像確認
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="p-1 bg-purple-100 rounded">
                      <History className="w-4 h-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        進捗トラッキング
                      </h4>
                      <p className="text-xs text-gray-600">
                        アップロード状況をリアルタイム表示
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="p-1 bg-orange-100 rounded">
                      <Settings className="w-4 h-4 text-orange-600" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">
                        自動検証
                      </h4>
                      <p className="text-xs text-gray-600">
                        ファイル形式・サイズの自動チェック
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 最近のアップロード */}
            {uploadedFiles.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    最近のアップロード
                  </h3>
                  <div className="space-y-3">
                    {uploadedFiles.slice(0, 5).map((file) => (
                      <div key={file.id} className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded overflow-hidden flex-shrink-0">
                          <img
                            src={file.preview}
                            alt={file.file.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {file.file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {file.status === 'completed' ? '完了' :
                             file.status === 'failed' ? '失敗' :
                             file.status === 'uploading' ? 'アップロード中' : '待機中'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;