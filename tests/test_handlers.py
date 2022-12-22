import os

import pytest
import logging
import pickle

from redis import Redis

from rlh import RedisLogHandler, RedisStreamLogHandler
from rlh.handlers import DEFAULT_FIELDS

# default values for Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)


@pytest.fixture
def redis_client():
    client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    # Making sure the stream is empty
    client.delete("logs")
    return client


@pytest.fixture
def log_record():
    return logging.LogRecord("", 0, "", 0, None, None, None)


@pytest.fixture
def logger():
    logging.basicConfig()
    logger = logging.getLogger('test_rlh')
    logger.setLevel(logging.INFO)
    return logger


class TestRedisLogHandler:

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


class TestRedisStreamLogHandler:

    def test_init_default_params(self):
        # Create a RedisStreamLogHandler instance with default params
        handler = RedisStreamLogHandler()
        # Assert that the attributes of the handler are set
        assert handler.stream_name == "logs"
        assert handler.fields == DEFAULT_FIELDS
        assert not handler.as_pkl

    def test_init_custom_params(self):
        # Create a RedisStreamLogHandler instance with custom fields
        handler = RedisStreamLogHandler(stream_name="test", fields=["lineno", "module"],
                                        as_pkl=True)
        # Assert that the attributes of the handler is correctly set
        assert handler.stream_name == "test"
        assert handler.fields == ["lineno", "module"]
        assert handler.as_pkl

    @pytest.mark.parametrize("input,expected", [
        # only valid fields
        (["msg", "levelno"], ["msg", "levelno"]),
        # empty fields
        ([], DEFAULT_FIELDS),
        # only invalid fields
        (["invalid_field_1", "invalid_field_2"], DEFAULT_FIELDS),
        # mixed invalid and valid fields
        (["msg", "levelno", "invalid_field_1", "invalid_field_2"], ["msg", "levelno"])
    ])
    def test_emit_log_fields(self, redis_client, logger, input, expected):
        # Create a RedisStreamLogHandler instance with custom fields
        handler = RedisStreamLogHandler(redis_client=redis_client,
                                        fields=input)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Testing log
        logger.info('Testing my redis logger')

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("logs", "-", "+")[-1]

        # Retrieve the data stored in Redis
        data = res[1]

        assert list(data.keys()) == expected

    def test_emit_as_pkl(self, logger):
        # Define a Redis client with 'decode_responses=False'
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
        # Create a RedisStreamLogHandler instance with as_pkl argument
        handler = RedisStreamLogHandler(redis_client=redis_client, as_pkl=True)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Testing log
        logger.info('Testing my redis logger')

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("logs", "-", "+")[-1]

        # Retrieve the data stored in Redis
        data = res[1]

        # Load the pickle log
        log = pickle.loads(data[b"pkl"])

        # We cannot perform a deep test as we cannot retrieve the LogRecord emitted
        assert log.msg == 'Testing my redis logger'
        assert log.levelname == 'INFO'

    def test_emit_custom_stream_name(self, redis_client, logger):
        # Create a RedisStreamLogHandler instance with custom stream_name
        handler = RedisStreamLogHandler(redis_client=redis_client,
                                        stream_name="test_name")

        # Add the handler to the logger
        logger.addHandler(handler)
        # Testing log
        logger.info('Testing my redis logger')

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("test_name", "-", "+")[-1]

        # Retrieve the data stored in Redis
        data = res[1]

        assert data["msg"] == 'Testing my redis logger'
        assert data["levelname"] == "INFO"
