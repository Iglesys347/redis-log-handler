import os
import logging

import pytest
from redis import Redis

# default values for Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)


@pytest.fixture
def redis_client():
    return Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@pytest.fixture
def redis_client_no_decode():
    return Redis(host=REDIS_HOST, port=REDIS_PORT)


@pytest.fixture
def log_record():
    return logging.LogRecord("", 0, "", 0, None, None, None)


@pytest.fixture
def logger():
    logging.basicConfig()
    log = logging.getLogger('test_rlh')
    log.handlers.clear()
    log.setLevel(logging.INFO)
    return log


@pytest.fixture(autouse=True)
def clean_redis_test_keys():
    yield
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT)
    for key in redis.keys("*test*"):
        redis.delete(key)
