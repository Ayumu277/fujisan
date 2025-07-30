# 画像アップロードAPI使用方法

## エンドポイント

### POST /api/v1/images/upload

画像ファイルをアップロードして保存します。

#### リクエスト

```bash
curl -X POST \
  "http://localhost:8000/api/v1/images/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/image.jpg"
```

#### レスポンス

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "20241030_1234_abcd1234_image.jpg",
  "status": "completed",
  "file_path": "/app/uploads/images/20241030_1234_abcd1234_image.jpg",
  "upload_date": "2024-10-30T12:34:56.789000",
  "thumbnail_path": "/app/uploads/thumbnails/20241030_1234_abcd1234_image_thumb.jpg",
  "file_size": 2048576
}
```

### GET /api/v1/images/{image_id}

指定されたIDの画像情報を取得します。

#### リクエスト

```bash
curl -X GET "http://localhost:8000/api/v1/images/550e8400-e29b-41d4-a716-446655440000"
```

### DELETE /api/v1/images/{image_id}

指定されたIDの画像を削除します。

#### リクエスト

```bash
curl -X DELETE "http://localhost:8000/api/v1/images/550e8400-e29b-41d4-a716-446655440000"
```

## セキュリティ機能

- ファイル拡張子検証
- MIMEタイプ検証
- ファイルサイズ制限 (10MB)
- ファイル署名検証
- ファイル名サニタイズ
- ウイルススキャン（プレースホルダー実装）

## サポートされる画像形式

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)

## 自動生成される機能

- ユニークなファイル名
- サムネイル画像 (200x200px)
- データベース記録
- EXIF情報の回転補正
