import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  Minimize2,
  Move,
  Search,
  Eye,
  EyeOff,
  Download,
  Share2,
} from 'lucide-react';

// 画像比較データの型定義
export interface ComparisonImage {
  id: string;
  url: string;
  title: string;
  metadata?: {
    width: number;
    height: number;
    size: number;
    format: string;
    uploadedAt: string;
  };
}

export interface SimilarityData {
  score: number;
  regions: Array<{
    id: string;
    x: number;
    y: number;
    width: number;
    height: number;
    confidence: number;
    type: 'match' | 'modification' | 'addition' | 'removal';
  }>;
}

interface ImageComparisonProps {
  originalImage: ComparisonImage;
  detectedImage: ComparisonImage;
  similarityData: SimilarityData;
  onRegionClick?: (regionId: string) => void;
  className?: string;
}

export const ImageComparison: React.FC<ImageComparisonProps> = ({
  originalImage,
  detectedImage,
  similarityData,
  onRegionClick,
  className = '',
}) => {
  // 状態管理
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showSimilarityRegions, setShowSimilarityRegions] = useState(true);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay' | 'slider'>('side-by-side');
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const originalImageRef = useRef<HTMLImageElement>(null);
  const detectedImageRef = useRef<HTMLImageElement>(null);

  // ズーム機能
  const handleZoomIn = useCallback(() => {
    setZoomLevel(prev => Math.min(prev * 1.5, 5));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel(prev => Math.max(prev / 1.5, 0.1));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  }, []);

  // パン（ドラッグ）機能
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (zoomLevel > 1) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - panOffset.x,
        y: e.clientY - panOffset.y,
      });
    }
  }, [zoomLevel, panOffset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && zoomLevel > 1) {
      setPanOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  }, [isDragging, dragStart, zoomLevel]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // キーボードショートカット
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case '+':
        case '=':
          e.preventDefault();
          handleZoomIn();
          break;
        case '-':
          e.preventDefault();
          handleZoomOut();
          break;
        case '0':
          e.preventDefault();
          handleZoomReset();
          break;
        case 'f':
        case 'F':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            setIsFullscreen(!isFullscreen);
          }
          break;
        case 's':
        case 'S':
          e.preventDefault();
          setShowSimilarityRegions(!showSimilarityRegions);
          break;
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleZoomIn, handleZoomOut, handleZoomReset, isFullscreen, showSimilarityRegions]);

  // 類似度領域のスタイル計算
  const getRegionStyle = (region: SimilarityData['regions'][0]) => {
    const colors = {
      match: 'rgba(34, 197, 94, 0.3)', // green
      modification: 'rgba(251, 191, 36, 0.3)', // yellow
      addition: 'rgba(59, 130, 246, 0.3)', // blue
      removal: 'rgba(239, 68, 68, 0.3)', // red
    };

    return {
      position: 'absolute' as const,
      left: `${region.x}%`,
      top: `${region.y}%`,
      width: `${region.width}%`,
      height: `${region.height}%`,
      backgroundColor: colors[region.type],
      border: `2px solid ${colors[region.type].replace('0.3', '1')}`,
      borderRadius: '4px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      zIndex: selectedRegion === region.id ? 20 : 10,
    };
  };

  // 画像のダウンロード
  const handleDownloadImage = useCallback(async (imageUrl: string, filename: string) => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  }, []);

  // 比較レポートのエクスポート
  const handleExportComparison = useCallback(() => {
    const comparisonData = {
      originalImage,
      detectedImage,
      similarityData,
      analysis: {
        zoomLevel,
        selectedRegions: similarityData.regions.filter(r => selectedRegion === r.id),
        timestamp: new Date().toISOString(),
      },
    };

    const dataStr = JSON.stringify(comparisonData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `image-comparison-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [originalImage, detectedImage, similarityData, zoomLevel, selectedRegion]);

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* ツールバー */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-gray-900">画像比較</h3>
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-blue-50 rounded-lg">
              <Search className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">
                類似度: {similarityData.score.toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* 表示モード切替 */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('side-by-side')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  viewMode === 'side-by-side'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                title="並べて表示"
              >
                並列
              </button>
              <button
                onClick={() => setViewMode('overlay')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  viewMode === 'overlay'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                title="オーバーレイ表示"
              >
                重ね
              </button>
              <button
                onClick={() => setViewMode('slider')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  viewMode === 'slider'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                title="スライダー表示"
              >
                スライダー
              </button>
            </div>

            <div className="w-px h-6 bg-gray-300"></div>

            {/* ズームコントロール */}
            <div className="flex items-center space-x-1">
              <button
                onClick={handleZoomOut}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="ズームアウト (-)"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-600 min-w-[4rem] text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="ズームイン (+)"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={handleZoomReset}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="リセット (0)"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            <div className="w-px h-6 bg-gray-300"></div>

            {/* その他のコントロール */}
            <button
              onClick={() => setShowSimilarityRegions(!showSimilarityRegions)}
              className={`p-2 transition-colors ${
                showSimilarityRegions
                  ? 'text-blue-600 hover:text-blue-700'
                  : 'text-gray-400 hover:text-gray-600'
              }`}
              title="類似度領域の表示切替 (S)"
            >
              {showSimilarityRegions ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </button>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="フルスクリーン (Ctrl+F)"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            <button
              onClick={handleExportComparison}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="比較データをエクスポート"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* メイン表示エリア */}
      <div
        ref={containerRef}
        className={`relative overflow-hidden bg-gray-50 ${
          isFullscreen ? 'fixed inset-0 z-50 bg-black' : 'h-96'
        }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: zoomLevel > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
      >
        {viewMode === 'side-by-side' && (
          <div className="flex h-full">
            {/* 元画像 */}
            <div className="flex-1 relative">
              <div className="absolute top-2 left-2 z-10 px-2 py-1 bg-black bg-opacity-75 text-white text-xs rounded">
                元画像
              </div>
              <div
                className="w-full h-full flex items-center justify-center"
                style={{
                  transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
                  transformOrigin: 'center',
                }}
              >
                <img
                  ref={originalImageRef}
                  src={originalImage.url}
                  alt="Original"
                  className="max-w-full max-h-full object-contain"
                />
                {/* 類似度領域の表示 */}
                {showSimilarityRegions && similarityData.regions.map((region) => (
                  <div
                    key={`orig-${region.id}`}
                    style={getRegionStyle(region)}
                    onClick={() => {
                      setSelectedRegion(region.id === selectedRegion ? null : region.id);
                      onRegionClick?.(region.id);
                    }}
                    className={selectedRegion === region.id ? 'ring-2 ring-blue-500' : ''}
                  />
                ))}
              </div>
            </div>

            {/* 区切り線 */}
            <div className="w-px bg-gray-300"></div>

            {/* 検出画像 */}
            <div className="flex-1 relative">
              <div className="absolute top-2 left-2 z-10 px-2 py-1 bg-black bg-opacity-75 text-white text-xs rounded">
                検出画像
              </div>
              <div
                className="w-full h-full flex items-center justify-center"
                style={{
                  transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
                  transformOrigin: 'center',
                }}
              >
                <img
                  ref={detectedImageRef}
                  src={detectedImage.url}
                  alt="Detected"
                  className="max-w-full max-h-full object-contain"
                />
                {/* 類似度領域の表示 */}
                {showSimilarityRegions && similarityData.regions.map((region) => (
                  <div
                    key={`det-${region.id}`}
                    style={getRegionStyle(region)}
                    onClick={() => {
                      setSelectedRegion(region.id === selectedRegion ? null : region.id);
                      onRegionClick?.(region.id);
                    }}
                    className={selectedRegion === region.id ? 'ring-2 ring-blue-500' : ''}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {viewMode === 'overlay' && (
          <div className="relative w-full h-full">
            <div
              className="absolute inset-0 flex items-center justify-center"
              style={{
                transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
                transformOrigin: 'center',
              }}
            >
              <img
                src={originalImage.url}
                alt="Original"
                className="absolute max-w-full max-h-full object-contain opacity-70"
              />
              <img
                src={detectedImage.url}
                alt="Detected"
                className="absolute max-w-full max-h-full object-contain opacity-70"
                style={{ mixBlendMode: 'difference' }}
              />
            </div>
          </div>
        )}

        {viewMode === 'slider' && (
          <div className="relative w-full h-full">
            <div
              className="absolute inset-0 flex items-center justify-center"
              style={{
                transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
                transformOrigin: 'center',
              }}
            >
              <div className="relative">
                <img
                  src={detectedImage.url}
                  alt="Detected"
                  className="max-w-full max-h-full object-contain"
                />
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
                >
                  <img
                    src={originalImage.url}
                    alt="Original"
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
              </div>
            </div>

            {/* スライダーコントロール */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
              <input
                type="range"
                min="0"
                max="100"
                value={sliderPosition}
                onChange={(e) => setSliderPosition(parseInt(e.target.value))}
                className="w-64 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* ズームレベルが1より大きい時のパンヒント */}
        {zoomLevel > 1 && !isDragging && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
            <div className="bg-black bg-opacity-75 text-white px-3 py-2 rounded-lg flex items-center space-x-2">
              <Move className="w-4 h-4" />
              <span className="text-sm">ドラッグして移動</span>
            </div>
          </div>
        )}
      </div>

      {/* 画像情報 */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">元画像情報</h4>
            <div className="space-y-1 text-xs text-gray-600">
              <div>タイトル: {originalImage.title}</div>
              {originalImage.metadata && (
                <>
                  <div>サイズ: {originalImage.metadata.width} × {originalImage.metadata.height}</div>
                  <div>ファイルサイズ: {(originalImage.metadata.size / 1024).toFixed(1)} KB</div>
                  <div>形式: {originalImage.metadata.format}</div>
                </>
              )}
            </div>
            <button
              onClick={() => handleDownloadImage(originalImage.url, `original-${originalImage.id}.jpg`)}
              className="mt-2 text-xs text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <Download className="w-3 h-3" />
              <span>ダウンロード</span>
            </button>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">検出画像情報</h4>
            <div className="space-y-1 text-xs text-gray-600">
              <div>タイトル: {detectedImage.title}</div>
              {detectedImage.metadata && (
                <>
                  <div>サイズ: {detectedImage.metadata.width} × {detectedImage.metadata.height}</div>
                  <div>ファイルサイズ: {(detectedImage.metadata.size / 1024).toFixed(1)} KB</div>
                  <div>形式: {detectedImage.metadata.format}</div>
                </>
              )}
            </div>
            <button
              onClick={() => handleDownloadImage(detectedImage.url, `detected-${detectedImage.id}.jpg`)}
              className="mt-2 text-xs text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <Download className="w-3 h-3" />
              <span>ダウンロード</span>
            </button>
          </div>
        </div>

        {/* 類似度領域の詳細 */}
        {showSimilarityRegions && similarityData.regions.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              類似度領域 ({similarityData.regions.length}個)
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {similarityData.regions.map((region) => (
                <div
                  key={region.id}
                  className={`p-2 rounded text-xs cursor-pointer transition-colors ${
                    selectedRegion === region.id
                      ? 'bg-blue-100 border-blue-300'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                  onClick={() => setSelectedRegion(region.id === selectedRegion ? null : region.id)}
                >
                  <div className="font-medium">{region.type}</div>
                  <div className="text-gray-600">信頼度: {region.confidence.toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageComparison;