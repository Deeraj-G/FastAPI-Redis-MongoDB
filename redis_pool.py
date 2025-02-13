import os
import redis
from redis.asyncio.client import PubSub
from dotenv import load_dotenv

load_dotenv()


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class RedisPoolProvider:
    """
    Define a class to initialize a connection from a redis pool
    """

    def __init__(self):
        # Need a container which starts with 'redis://'
        # self.redis_pool = redis.asyncio.ConnectionPool(url=REDIS_URL, decode_responses=True)
        self.redis_client = redis.asyncio.Redis(
            host="localhost", port=6379, decode_responses=True
        )

    # return an asyncio PubSub object
    def pubsub(self) -> PubSub:
        return self.redis_client.pubsub()

    # set a value for this specific redis_key
    def set(self, redis_key, value):
        return self.redis_client.set(name=redis_key, value=value)

    # cleanup - close the client
    async def close(self):
        await self.redis_client.close()


# publish to existing channel
async def publish(
    redis: RedisPoolProvider,
    channel: str = "default",
    message="",
):
    await redis.redis_client.publish(channel, message)
    return "published"


# establish and subscribe to channel
async def subscribe(channel: str, redis: RedisPoolProvider):
    pubsub = redis.pubsub()
    # access the subscribe method as part of PubSub class
    await pubsub.subscribe(channel)
    await publish(redis=redis, channel=channel)

    # TODO: Need to introduce timeout mechanism
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                print(f"Received: {message['data']} on {channel}")
                yield {"event": "message", "data": message["data"]}

    except Exception as e:
        print(f"Error while listening to {channel}: {e}")
    finally:
        await pubsub.unsubscribe(channel)
