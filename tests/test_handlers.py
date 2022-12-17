import os

import pytest
from logging import LogRecord

from redis import Redis

from rlh import RedisLogHandler

# default values for Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)


class TestRedisLogHandler:

    @pytest.fixture
    def redis_client(self):
        return Redis(host=REDIS_HOST, port=REDIS_PORT)

    @pytest.fixture
    def log_record(self):
        return LogRecord("", 0, "", 0, None, None, None)

    def test_init_redis_client(self, redis_client):
        # Create a RedisLogHandler instance with the Redis client
        handler = RedisLogHandler(redis_client=redis_client)
        # Assert that the redis attribute of the handler is the client
        assert handler.redis is redis_client

    def test_init_redis_extra_args(self):
        # Create a RedisLogHandler instance with extra keyword arguments
        handler = RedisLogHandler(check_conn=False, host="redis", port=6969, db=1,
                                  decode_responses=True, password="secret")
        # Assert that the extra arguments were passed to the redis client
        redis_args = handler.redis.get_connection_kwargs()
        assert redis_args["host"] == "redis"
        assert redis_args["port"] == 6969
        assert redis_args["db"] == 1
        assert redis_args["decode_responses"]
        assert redis_args["password"] == "secret"

    def test_init_invalid_redis_args(self):
        with pytest.raises(TypeError):
            # Create a RedisLogHandler instance with invalid Redis arguments
            RedisLogHandler(invalidargument="invalid")

    def test_init_unreachable_redis(self):
        with pytest.raises(ConnectionError):
            # Create a RedisLogHandler instance with an unreachable Redis client
            RedisLogHandler(host="redis", port=6969)

    def test_init_unreachable_redis_ignored(self):
        # Create a RedisLogHandler instance with an unreachable Redis client
        # but not checking connection
        RedisLogHandler(check_conn=False, host="redis", port=6969)

    def test_emit_not_implemented(self, redis_client, log_record):
        # Create a RedisLogHandler instance
        handler = RedisLogHandler(redis_client=redis_client)
        with pytest.raises(NotImplementedError):
            handler.emit(log_record)
