import json
import pickle

import pytest

from rlh import RedisLogHandler, RedisStreamLogHandler, RedisPubSubLogHandler
from rlh.handlers import DEFAULT_FIELDS


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

    def test_buffer_emit_not_implemented(self, redis_client):
        handler = RedisLogHandler(redis_client=redis_client)
        with pytest.raises(NotImplementedError):
            handler._buffer_emit()


class TestRedisStreamLogHandler:

    def test_init_default_params(self):
        # Create a RedisStreamLogHandler instance with default params
        handler = RedisStreamLogHandler()
        # Assert that the attributes of the handler are set
        assert handler.stream_name == "logs"
        assert handler.maxlen == None
        assert handler.approximate
        assert handler.fields == DEFAULT_FIELDS
        assert not handler.as_pkl

    def test_init_custom_params(self):
        # Create a RedisStreamLogHandler instance with custom fields
        handler = RedisStreamLogHandler(stream_name="test", maxlen=10, approximate=False,
                                        fields=["lineno", "module"], as_pkl=True)
        # Assert that the attributes of the handler is correctly set
        assert handler.stream_name == "test"
        assert handler.maxlen == 10
        assert not handler.approximate
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
                                        fields=input, stream_name="test_logs")

        # Add the handler to the logger
        logger.addHandler(handler)
        # Testing log
        logger.info('Testing my redis logger')

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("test_logs", "-", "+")[-1]

        # Retrieve the data stored in Redis
        data = res[1]

        assert list(data.keys()) == expected

    def test_emit_as_pkl(self, redis_client_no_decode, logger):
        # Create a RedisStreamLogHandler instance with as_pkl argument
        handler = RedisStreamLogHandler(redis_client=redis_client_no_decode,
                                        as_pkl=True, stream_name="test_logs")

        # Add the handler to the logger
        logger.addHandler(handler)
        # Testing log
        logger.info('Testing my redis logger')

        # Retrieve the last log saved in Redis
        res = redis_client_no_decode.xrange("test_logs", "-", "+")[-1]

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

    def test_emit_bath(self, redis_client, logger):
        # Create a RedisStreamLogHandler instance with batch size
        handler = RedisStreamLogHandler(redis_client=redis_client, stream_name="test_name",
                                        batch_size=10)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Addin only one log
        logger.info('Testing my redis logger 0')

        # Cheching that the log has been added to the bufer
        assert len(handler.log_buffer) == 1
        assert handler.log_buffer[0]["msg"] == 'Testing my redis logger 0'
        assert handler.log_buffer[0]["levelname"] == "INFO"

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("test_name", "-", "+")
        # Checking that the log has not been pushed to Redis
        assert res == []

        # Adding more logs to the handler
        for i in range(1, 10):
            logger.info('Testing my redis logger %s', i)

        # Checking the 10 batched logs have been emitted
        res = redis_client.xrange("test_name", "-", "+")
        # Checking that the logs has been pushed to Redis
        assert res != []
        for i, elt in enumerate(res):
            data = elt[1]
            assert data["msg"] == f'Testing my redis logger {i}'
            assert data["levelname"] == "INFO"

    def test_emit_bath_del(self, redis_client, logger):
        # Create a RedisStreamLogHandler instance with batch size
        handler = RedisStreamLogHandler(redis_client=redis_client, stream_name="test_name",
                                        batch_size=10)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Addin only one log
        logger.info('Testing my redis logger')

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("test_name", "-", "+")
        # Checking that the log has not been pushed to Redis
        assert res == []

        # Closing the handler
        handler.close()

        # Retrieve the last log saved in Redis
        res = redis_client.xrange("test_name", "-", "+")[-1]
        # Retrieve the data stored in Redis
        data = res[1]

        assert data["msg"] == 'Testing my redis logger'
        assert data["levelname"] == "INFO"

    def test_emit_stream_maxlen(self, redis_client, logger):
        # Create a RedisStreamLogHandler instance with fixed maxlen = 5
        handler = RedisStreamLogHandler(redis_client=redis_client, stream_name="test_name",
                                        maxlen=5, approximate=False)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Adding 10 logs
        for i in range(10):
            logger.info('Testing my redis logger %s', i)

        # Checking that the Redis stream size is equals to maxlen (5)
        assert redis_client.xlen("test_name") == 5

    def test_emit_stream_approximate_maxlen(self, redis_client, logger):
        # Create a RedisStreamLogHandler instance with approximate maxlen = 5
        handler = RedisStreamLogHandler(redis_client=redis_client, stream_name="test_name",
                                        maxlen=5, approximate=True)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Adding 10 logs
        for i in range(10):
            logger.info('Testing my redis logger %s', i)

        # Checking that the Redis stream contains at least 5 element
        assert redis_client.xlen("test_name") >= 5

class TestRedisPubSubLogHandler:

    def test_init_default_params(self):
        # Create a RedisPubSubLogHandler instance with default params
        handler = RedisPubSubLogHandler()
        # Assert that the attributes of the handler are set
        assert handler.channel_name == "logs"
        assert handler.fields == DEFAULT_FIELDS
        assert not handler.as_pkl

    def test_init_custom_params(self):
        # Create a RedisPubSubLogHandler instance with custom fields
        handler = RedisPubSubLogHandler(channel_name="test", fields=["lineno", "module"],
                                        as_pkl=True)
        # Assert that the attributes of the handler is correctly set
        assert handler.channel_name == "test"
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
        # Create a RedisPubSubLogHandler instance with custom fields
        handler = RedisPubSubLogHandler(redis_client=redis_client,
                                        fields=input, channel_name="test_logs")

        # Add the handler to the logger
        logger.addHandler(handler)

        p = redis_client.pubsub()
        # Subscribe to channel
        p.subscribe("test_logs")

        # Retrieving subscribe message
        assert p.get_message(timeout=10)["type"] == "subscribe"

        # Testing log
        logger.info('Testing my redis logger')
        # Removing the handler from the logger
        logger.handlers.clear()

        # Retrieve the last log saved in Redis
        mess = p.get_message(ignore_subscribe_messages=True, timeout=10)
        # Retrieve the data stored in Redis
        data = json.loads(mess["data"])

        assert list(data.keys()) == expected

    def test_emit_as_pkl(self, redis_client_no_decode, logger):
        # Create a RedisPubSubLogHandler instance with as_pkl argument
        handler = RedisPubSubLogHandler(redis_client=redis_client_no_decode, as_pkl=True,
                                        channel_name="test_logs")

        # Add the handler to the logger
        logger.addHandler(handler)

        p = redis_client_no_decode.pubsub()
        # Subscribe to channel
        p.subscribe("test_logs")

        # Retrieving subscribe message
        assert p.get_message(timeout=10)["type"] == "subscribe"

        # Testing log
        logger.info('Testing my redis logger')
        # Removing the handler from the logger
        logger.handlers.clear()

        # Sleeping for 1 sec before retrieving the log
        # time.sleep(1)
        # Retrieve the last log saved in Redis
        mess = p.get_message(ignore_subscribe_messages=True, timeout=10)
        # Retrieve the data stored in Redis
        data = mess["data"]

        # Load the pickle log
        log = pickle.loads(data)

        # We cannot perform a deep test as we cannot retrieve the LogRecord emitted
        assert log.msg == 'Testing my redis logger'
        assert log.levelname == 'INFO'

    def test_emit_bath(self, redis_client, logger):
        # Create a RedisPubSub instance with batch size
        handler = RedisPubSubLogHandler(redis_client=redis_client, channel_name="test_name",
                                        batch_size=10)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Addin only one log
        logger.info('Testing my redis logger 0')

        p = redis_client.pubsub()
        # Subscribe to channel
        p.subscribe("test_name")

        # Cheching that the log has been added to the bufer
        assert len(handler.log_buffer) == 1
        log = json.loads(handler.log_buffer[0])
        # We cannot perform a deep test as we cannot retrieve the LogRecord emitted
        assert log["msg"] == 'Testing my redis logger 0'
        assert log["levelname"] == 'INFO'

        mess = p.get_message(ignore_subscribe_messages=True, timeout=10)
        assert mess == None

        # Adding more logs to the handler
        for i in range(1, 10):
            logger.info('Testing my redis logger %s', i)

        # Checking the 10 batched logs have been emitted
        for i in range(10):
            mess = p.get_message(ignore_subscribe_messages=True, timeout=10)
            # Checking that the logs has been pushed to Redis
            assert mess is not None
            log = json.loads(mess["data"])
            assert log["msg"] == f'Testing my redis logger {i}'
            assert log["levelname"] == "INFO"

    def test_emit_bath_del(self, redis_client, logger):
        # Create a RedisPubSub instance with batch size
        handler = RedisPubSubLogHandler(redis_client=redis_client, channel_name="test_name",
                                        batch_size=10)

        # Add the handler to the logger
        logger.addHandler(handler)
        # Addin only one log
        logger.info('Testing my redis logger')

        p = redis_client.pubsub()
        # Subscribe to channel
        p.subscribe("test_name")

        # Retrieve the last log saved in Redis
        mess = p.get_message(ignore_subscribe_messages=True, timeout=10)
        # Checking that the log has not been pushed to Redis
        assert mess == None

        # Closing the handler
        handler.close()

        # Retrieve the last log saved in Redis
        mess = p.get_message(ignore_subscribe_messages=True, timeout=10)
        log = json.loads(mess["data"])
        assert log["msg"] == 'Testing my redis logger'
        assert log["levelname"] == "INFO"