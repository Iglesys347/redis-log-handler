"""
This module contains handlers that can be used to forward logs from python logging module
to a Redis database.
"""

import logging
import pickle

import redis

DEFAULT_FIELDS = [
    "msg",          # the log message
    "levelname",    # the log level
    "created"       # the log timestamp
]


class RedisLogHandler(logging.Handler):
    """
    Default class for Redis log handlers.

    Attributes
    ----------
    redis : redis.Redis
        The Redis client.

    Methods
    -------
    emit(record: logging.LogRecord)
        This method is intended to be implemented by subclasses and so raises a NotImplementedError.
    """

    def __init__(self, redis_client=None, check_conn=True, **redis_args) -> None:
        super().__init__()

        if redis_client is not None:
            self.redis = redis_client
        else:
            try:
                self.redis = redis.Redis(**redis_args)
            except TypeError as err:
                raise TypeError(
                    "One of the argument passed to Redis is not valid") from err

        if check_conn:
            # trying to ping Redis DB
            try:
                self.redis.ping()
            except redis.exceptions.ConnectionError as err:
                raise ConnectionError("Unable to ping Redis DB") from err

    def emit(self, record: logging.LogRecord) -> None:
        raise NotImplementedError(
            "emit must be implemented by RedisLogHandler subclasses")


class RedisStreamLogHandler(RedisLogHandler):
    """
    Handler used to forward logs to a Redis stream.

    Attributes
    ----------
    redis : redis.Redis
        The Redis client.
    stream_name : str
        The name of the Redis stream.
    fields : list(str)
        The list of logs fields to forward.
    as_pkl : bool
        If true, the logs are written as pickle format in the stream.

    Methods
    -------
    emit(record: logging.LogRecord)
        Forward log to the Redis stream.

    See also
    --------
    redis streams: https://redis.io/docs/data-types/streams/
    """

    def __init__(self, redis_client=None, check_conn=True, stream_name="logs",
                 fields=None, as_pkl=False, **redis_args) -> None:
        super().__init__(redis_client, check_conn, **redis_args)

        self.stream_name = stream_name
        self.as_pkl = as_pkl

        self.fields = fields if fields is not None else DEFAULT_FIELDS

    def emit(self, record):
        """
        Write the log record in the Redis stream.

        Every time a log is emitted, an entry is inserted in the stream.
        This entry is a dict that has the following format:
            - If `as_pkl` is set to true, the records are saved as their pickle format
            with the key "pkl"
            - Otherwise we use the different fields as keys and their associated value
            in the record as the value
        """
        if self.as_pkl:
            stream_entry = {"pkl": pickle.dumps(record)}
        else:
            stream_entry = _make_fields(record, self.fields)

        self.redis.xadd(self.stream_name, stream_entry)


def _make_fields(record, fields):
    """
    Return the fields dict for the log record.

    If all the specified fields are invalid, use the default fields.
    """
    field_dict = {field: getattr(record, field)
                  for field in fields if hasattr(record, field)}

    if field_dict == {}:
        return {field: getattr(record, field)
                for field in DEFAULT_FIELDS if hasattr(record, field)}
    return field_dict
