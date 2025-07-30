"""
ABDSシステム - セキュリティユーティリティ
ファイルセキュリティ検証、ウイルススキャン、MIMEタイプ検証
"""

import os
import magic
import hashlib
from typing import Optional, Dict, List
from pathlib import Path

# ファイル署名（マジックナンバー）による検証
FILE_SIGNATURES = {
    # 画像形式
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a': 'image/png',
    b'\x47\x49\x46\x38': 'image/gif',
    b'\x42\x4d': 'image/bmp',
    b'\x52\x49\x46\x46': 'image/webp',  # RIFF header (WebP)
}

# 危険なファイル拡張子
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar', 
    '.app', '.deb', '.pkg', '.rpm', '.dmg', '.iso', '.msi', '.dll', '.so', 
    '.dylib', '.php', '.asp', '.jsp', '.py', '.rb', '.pl', '.sh', '.ps1'
}

# 許可されるMIMEタイプ（画像のみ）
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp'
}


def check_file_signature(file_path: str) -> Optional[str]:
    """
    ファイルの署名（マジックナンバー）をチェック
    
    Args:
        file_path: チェックするファイルのパス
        
    Returns:
        検出されたMIMEタイプ、検出できない場合はNone
    """
    try:
        with open(file_path, 'rb') as f:
            file_header = f.read(16)  # 最初の16バイトを読む
        
        for signature, mime_type in FILE_SIGNATURES.items():
            if file_header.startswith(signature):
                return mime_type
        
        return None
        
    except Exception:
        return None


def validate_mime_type(file_path: str, declared_mime_type: Optional[str] = None) -> bool:
    """
    MIMEタイプの検証
    
    Args:
        file_path: 検証するファイルのパス
        declared_mime_type: 宣言されたMIMEタイプ
        
    Returns:
        有効なMIMEタイプの場合True
    """
    try:
        # libmagicを使用した実際のMIMEタイプ検出
        actual_mime_type = magic.from_file(file_path, mime=True)
        
        # 許可されたMIMEタイプかチェック
        if actual_mime_type not in ALLOWED_MIME_TYPES:
            return False
        
        # 宣言されたMIMEタイプとの一致チェック（ある場合）
        if declared_mime_type:
            # 一般的なMIME型の正規化
            normalized_declared = declared_mime_type.lower().strip()
            normalized_actual = actual_mime_type.lower().strip()
            
            # JPEG の場合、image/jpg と image/jpeg を同じとして扱う
            if normalized_declared == 'image/jpg':
                normalized_declared = 'image/jpeg'
            if normalized_actual == 'image/jpg':
                normalized_actual = 'image/jpeg'
            
            if normalized_declared != normalized_actual:
                return False
        
        # ファイル署名による二重チェック
        signature_mime = check_file_signature(file_path)
        if signature_mime and signature_mime != actual_mime_type:
            # 署名とlibmagicの結果が異なる場合は疑わしい
            return False
        
        return True
        
    except Exception:
        return False


def check_dangerous_extension(filename: str) -> bool:
    """
    危険なファイル拡張子のチェック
    
    Args:
        filename: チェックするファイル名
        
    Returns:
        危険な拡張子の場合True
    """
    if not filename:
        return True
    
    # 拡張子を取得して小文字に変換
    _, ext = os.path.splitext(filename.lower())
    
    return ext in DANGEROUS_EXTENSIONS


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    ファイルのハッシュ値を計算
    
    Args:
        file_path: ファイルのパス
        algorithm: ハッシュアルゴリズム
        
    Returns:
        ハッシュ値、計算できない場合はNone
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception:
        return None


def scan_file_for_virus(file_path: str) -> Dict[str, any]:
    """
    ウイルススキャンの実行
    
    注意: この実装はプレースホルダーです。
    実際の本番環境では、ClamAV、VirusTotal API、または
    その他のウイルススキャンソリューションを統合してください。
    
    Args:
        file_path: スキャンするファイルのパス
        
    Returns:
        スキャン結果の辞書
    """
    # TODO: 実際のウイルススキャン実装
    # 例: ClamAVとの統合
    # import pyclamd
    # cd = pyclamd.ClamdUnixSocket()
    # scan_result = cd.scan_file(file_path)
    
    # TODO: VirusTotal APIとの統合
    # import requests
    # VT_API_KEY = settings.VIRUSTOTAL_API_KEY
    # url = "https://www.virustotal.com/vtapi/v2/file/scan"
    
    # 現在はダミー実装
    result = {
        'clean': True,
        'threats_found': [],
        'scan_engine': 'placeholder',
        'scan_time': 0.0,
        'file_hash': calculate_file_hash(file_path),
        'message': 'プレースホルダー実装: 実際のウイルススキャンが必要です'
    }
    
    # 基本的な危険ファイルチェック
    filename = os.path.basename(file_path)
    if check_dangerous_extension(filename):
        result['clean'] = False
        result['threats_found'].append('dangerous_file_extension')
        result['message'] = '危険なファイル拡張子が検出されました'
    
    return result


def validate_file_content(file_path: str) -> Dict[str, any]:
    """
    ファイル内容の包括的な検証
    
    Args:
        file_path: 検証するファイルのパス
        
    Returns:
        検証結果の辞書
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'file_info': {}
    }
    
    try:
        # ファイルの存在確認
        if not os.path.exists(file_path):
            result['valid'] = False
            result['errors'].append('ファイルが存在しません')
            return result
        
        # ファイルサイズチェック
        file_size = os.path.getsize(file_path)
        result['file_info']['size'] = file_size
        
        if file_size == 0:
            result['valid'] = False
            result['errors'].append('ファイルが空です')
            return result
        
        # MIMEタイプ検証
        if not validate_mime_type(file_path):
            result['valid'] = False
            result['errors'].append('不正なMIMEタイプです')
        
        # 危険な拡張子チェック
        filename = os.path.basename(file_path)
        if check_dangerous_extension(filename):
            result['valid'] = False
            result['errors'].append('危険なファイル拡張子です')
        
        # ウイルススキャン
        virus_scan = scan_file_for_virus(file_path)
        result['virus_scan'] = virus_scan
        
        if not virus_scan['clean']:
            result['valid'] = False
            result['errors'].append('ウイルスまたは脅威が検出されました')
        
        # ファイルハッシュ計算
        result['file_info']['hash'] = calculate_file_hash(file_path)
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f'検証中にエラーが発生しました: {str(e)}')
    
    return result


def sanitize_upload_directory(upload_dir: str) -> bool:
    """
    アップロードディレクトリのセキュリティチェック
    
    Args:
        upload_dir: チェックするディレクトリ
        
    Returns:
        安全な場合True
    """
    try:
        upload_path = Path(upload_dir).resolve()
        
        # 相対パス攻撃の防止
        if '..' in str(upload_path):
            return False
        
        # システムディレクトリへのアクセス防止
        system_dirs = ['/bin', '/sbin', '/etc', '/sys', '/proc', '/root']
        for sys_dir in system_dirs:
            if str(upload_path).startswith(sys_dir):
                return False
        
        return True
        
    except Exception:
        return False
