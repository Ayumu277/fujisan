"""
ABDSシステム - Redis接続設定
キャッシュとセッション管理
"""

import redis.asyncio as redis
from typing import Optional
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Redisクライアントのラッパークラス
    """

    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """
        Redis接続の初期化
        """
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # 接続テスト
            await self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None

    async def close(self):
        """
        Redis接続のクローズ
        """
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """
        キーから値を取得
        """
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """
        キーと値を設定
        """
        if not self.redis:
            return False
        try:
            if expire:
                await self.redis.setex(key, expire, value)
            else:
                await self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        キーを削除
        """
        if not self.redis:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def get_json(self, key: str) -> Optional[dict]:
        """
        JSONデータを取得
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in Redis key: {key}")
        return None

    async def set_json(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        """
        JSONデータを設定
        """
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, expire)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        キーの存在確認
        """
        if not self.redis:
            return False
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """
        キーに有効期限を設定
        """
        if not self.redis:
            return False
        try:
            return bool(await self.redis.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

# グローバルなRedisクライアントインスタンス
redis_client = RedisClient()