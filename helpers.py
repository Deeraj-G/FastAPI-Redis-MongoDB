import json
import os
from typing import Union
from uuid import UUID

from bson.binary import UUID_SUBTYPE, Binary
from dotenv import load_dotenv
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession

from models import Item
from redis_pool import RedisPoolProvider, publish

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")


# Establish the mongodb client
async def get_mongo_client():
    return await AsyncIOMotorClient(MONGODB_URL)


# Get the db from the mongo client
# TODO: there's a better way to start a session, current impl. is insufficient
async def get_db_from_mongo_client(mongo_client: AsyncIOMotorClientSession, db_name: str):
    return await mongo_client.get_database(db_name)


# Simplify the return
async def send_response(
    content,
    status_code,
    pub: bool,
    redis_client: RedisPoolProvider = Depends(RedisPoolProvider),
    redis_key: Union[str, None] = None,
):
    # publish to redis channel only if needed
    if pub:
        await publish(redis_client, redis_key, json.dumps(content))

    # return JSON object
    return {"content": content, "status": status_code}


# Convert UUID of type str to bson Binary for db field with 'bsonType: binData'
def convert_to_bson_binary(value):
    return Binary(UUID(value).bytes, UUID_SUBTYPE)
