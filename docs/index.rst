.. redis-log-handler documentation master file, created by
   sphinx-quickstart on Fri Jan  6 11:53:37 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to redis-log-handler's documentation!
=============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Installation
************

Install the package `redis-logs` using `pip`:

.. code-block:: bash

   pip install redis-logs

You can then import the handlers from `rlh` module, for example:

.. code-block:: python

   from rlh import RedisStreamLogHandler


Basic example
*************

Setup log forwarding to a redis stream:

.. code-block:: python

   from rlh import RedisStreamLogHandler

   # define your logger
   logger = logging.getLogger('my_app')

   # define the Redis log handler
   handler = RedisStreamLogHandler()
   # add the handler to the logger
   logger.addHandler(handler)

After that, all the logs emitted with the logger will be forwarded to a Redis Stream; by default the logs are forwarded to a Redis instance running at localhost:6379 in a stream named logs.


Module Documentation
********************
.. toctree::
   :maxdepth: 1

   handlers
