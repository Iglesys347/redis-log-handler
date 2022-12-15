# redis-log-handler

Log handler to forward logs to Redis

| [Installation](#installation) | [Usage](#usage) |
| :---------------------------: | :-------------: |

## Installation

Installation with `pip`:

```bash
pip install redis-logs
```

## Usage

### Basic example

Setup log forwarding to a redis stream:

```python
from rlh import RedisStreamLogHandler

# define your logger
logger = logging.getLogger('my_app')

# define the Redis log handler
handler = RedisStreamLogHandler()
# add the handler to the logger
logger.addHandler(handler)
```

After that, all the logs emitted with the logger will be forwarded to a [Redis Stream](https://redis.io/docs/data-types/streams/); by default the logs are forwarded to a Redis instance running at `localhost:6379` in a stream named `logs`.

### Use a different stream name

```python
from rlh import RedisStreamLogHandler

# define your logger
logger = logging.getLogger('my_app')

# define the Redis log handler
handler = RedisStreamLogHandler(stream_name="custom_stream_name")
# add the handler to the logger
logger.addHandler(handler)
```

### Specify a custom Redis client

To use a custom Redis client, you can either define your own client with `redis.Redis` and then pass it to the handler:

```python
from redis import Redis
from rlh import RedisStreamLogHandler

# define a custom Redis client
client = Redis(host="redis", port=6380, db=1)

# define your logger
logger = logging.getLogger('my_app')

# define the Redis log handler with custom Redis client
handler = RedisStreamLogHandler(redis_client=client)
# add the handler to the logger
logger.addHandler(handler)
```

Or dirrectly call the handler constructor with your custom Redis settings:

```python
from rlh import RedisStreamLogHandler

# define your logger
logger = logging.getLogger('my_app')

# define the Redis log handler with custom Redis client
handler = RedisStreamLogHandler(host="redis", port=6380, db=1)
# add the handler to the logger
logger.addHandler(handler)
```

### Specify custom log fields to save

By default the handler only saves the logs fieds `msg`, `levelname` and `created`. You can however change this default behaviour by setting your own desired fields (see the full list of fields in [logging documentation](https://docs.python.org/3/library/logging.html#logrecord-attributes)):

```python
from rlh import RedisStreamLogHandler

# define your logger
logger = logging.getLogger('my_app')

# define the Redis log handler with custom fields
handler = RedisStreamLogHandler(fields=["msg", "name", "module", "levelno"])
# add the handler to the logger
logger.addHandler(handler)
```

### Save `LogRecord` as pickle format

Logs can also be saved in DB as [pickle format](https://docs.python.org/3/library/pickle.html):

```python
from rlh import RedisStreamLogHandler

# define your logger
logger = logging.getLogger('my_app')

# define the Redis log handler with custom fields
handler = RedisStreamLogHandler(as_pkl=True)
# add the handler to the logger
logger.addHandler(handler)
```

This can be useful if you need to re-use the logs with another python program.
