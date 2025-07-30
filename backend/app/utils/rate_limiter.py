"""
ABDSシステム - レート制限機能
APIレート制限とリクエスト管理
"""

import time
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    レート制限機能
    指定された時間窓内でのリクエスト回数を制限
    """
    
    def __init__(self, limit: int, window: int):
        """
        Args:
            limit: 制限回数
            window: 時間窓（秒）
        """
        self.limit = limit
        self.window = window
        self.requests = deque()
        self.lock = threading.Lock()
        
    async def acquire(self, key: str = "default") -> bool:
        """
        レート制限チェックとリクエスト許可
        
        Args:
            key: レート制限のキー（ユーザーIDなど）
            
        Returns:
            許可された場合True、制限に達した場合False
        """
        current_time = time.time()
        
        with self.lock:
            # 時間窓外の古いリクエストを削除
            while self.requests and self.requests[0] <= current_time - self.window:
                self.requests.popleft()
            
            # 制限チェック
            if len(self.requests) >= self.limit:
                next_allowed = self.requests[0] + self.window
                wait_time = next_allowed - current_time
                logger.warning(f"レート制限に達しました。{wait_time:.1f}秒後に再試行可能")
                return False
            
            # リクエストを記録
            self.requests.append(current_time)
            return True
    
    def get_remaining_requests(self) -> int:
        """残りリクエスト数を取得"""
        current_time = time.time()
        
        with self.lock:
            # 時間窓外の古いリクエストを削除
            while self.requests and self.requests[0] <= current_time - self.window:
                self.requests.popleft()
            
            return max(0, self.limit - len(self.requests))
    
    def get_reset_time(self) -> Optional[datetime]:
        """制限リセット時刻を取得"""
        if not self.requests:
            return None
            
        with self.lock:
            oldest_request = self.requests[0]
            reset_time = oldest_request + self.window
            return datetime.fromtimestamp(reset_time)


class GlobalRateLimiter:
    """
    グローバルレート制限機能
    複数のキーに対してレート制限を管理
    """
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.lock = threading.Lock()
    
    def get_limiter(self, key: str, limit: int, window: int) -> RateLimiter:
        """指定されたキーのレート制限機能を取得"""
        with self.lock:
            if key not in self.limiters:
                self.limiters[key] = RateLimiter(limit, window)
            return self.limiters[key]
    
    async def acquire(self, key: str, limit: int, window: int) -> bool:
        """レート制限チェック"""
        limiter = self.get_limiter(key, limit, window)
        return await limiter.acquire()


# グローバルインスタンス
global_rate_limiter = GlobalRateLimiter()


# =================================
# FastAPI用のレート制限デコレータ
# =================================

def rate_limit(limit: int, window: int):
    """
    FastAPIエンドポイント用のレート制限デコレータ
    
    Args:
        limit: 制限回数
        window: 時間窓（秒）
    """
    def decorator(func):
        limiter = RateLimiter(limit, window)
        
        async def wrapper(*args, **kwargs):
            if not await limiter.acquire():
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="レート制限に達しました。後でもう一度お試しください。"
                )
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =================================
# Redis基盤のレート制限（将来の拡張用）
# =================================

class RedisRateLimiter:
    """
    Redis基盤のレート制限機能
    分散環境でのレート制限に対応
    """
    
    def __init__(self, redis_client, limit: int, window: int):
        """
        Args:
            redis_client: Redis クライアント
            limit: 制限回数
            window: 時間窓（秒）
        """
        self.redis = redis_client
        self.limit = limit
        self.window = window
    
    async def acquire(self, key: str) -> bool:
        """
        Redis基盤のレート制限チェック
        
        TODO: 実際のRedis実装
        - INCR + EXPIRE を使用したカウンター方式
        - または sliding window log 方式
        """
        # プレースホルダー実装
        return True


# =================================
# 使用例とテスト
# =================================

# TODO: レート制限のテスト実装
#
# async def test_rate_limiter():
#     """レート制限のテスト"""
#     limiter = RateLimiter(limit=5, window=60)  # 1分間に5回
#     
#     # 5回のリクエストは成功する
#     for i in range(5):
#         result = await limiter.acquire()
#         assert result is True, f"Request {i+1} should succeed"
#     
#     # 6回目は失敗する
#     result = await limiter.acquire()
#     assert result is False, "6th request should be rate limited"
#     
#     print("レート制限テスト完了")
#
# if __name__ == "__main__":
#     asyncio.run(test_rate_limiter())
