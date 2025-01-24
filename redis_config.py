import redis
import os
from typing import Optional
import logging
import json
from ast import literal_eval

class RedisConfig:
    def __init__(self):
        self.logger = self._setup_logger()
        self.redis_client = self._initialize_redis()
        self.CACHE_EXPIRATION = 60 * 60 * 24  # 24 hours

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('RedisConfig')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _initialize_redis(self) -> Optional[redis.Redis]:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://default:B058xThhTvAbptQa0s25EAGk7A5u473O@redis-13833.c336.samerica-east1-1.gce.redns.redis-cloud.com:13833")
            client = redis.from_url(redis_url)
            client.ping()
            self.logger.info("Connected to Redis via URL")
            return client
        except:
            try:
                client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'redis-13833.c336.samerica-east1-1.gce.redns.redis-cloud.com'),
                    port=int(os.getenv('REDIS_PORT', 13833)),
                    password=os.getenv('REDIS_PASSWORD', 'B058xThhTvAbptQa0s25EAGk7A5u473O'),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                client.ping()
                self.logger.info("Connected to Redis via parameters")
                return client
            except Exception as e:
                self.logger.error(f"Redis connection failed: {str(e)}")
                return None

    def get_cached_result(self, concurso: int) -> Optional[dict]:
        if not self.redis_client:
            return None
            
        try:
            cached = self.redis_client.get(f"megasena:{concurso}")
            if not cached:
                return None
            try:
                return json.loads(cached)
            except:
                try:
                    return literal_eval(cached)
                except:
                    return None
        except Exception as e:
            self.logger.error(f"Cache retrieval error for contest {concurso}: {str(e)}")
            return None

    def set_cached_result(self, concurso: int, data: dict) -> bool:
        if not self.redis_client:
            return False
            
        try:
            serialized = json.dumps(data, ensure_ascii=False)
            self.redis_client.setex(
                f"megasena:{concurso}", 
                self.CACHE_EXPIRATION, 
                serialized
            )
            return True
        except Exception as e:
            self.logger.error(f"Cache storage error for contest {concurso}: {str(e)}")
            return False

redis_config = RedisConfig()