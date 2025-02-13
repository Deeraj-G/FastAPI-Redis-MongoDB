import os
import json
from bson.binary import Binary, UUID_SUBTYPE
from typing import Union
from fastapi import Depends
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from redis_pool import RedisPoolProvider, publish
from dotenv import load_dotenv
from uuid import UUID

from models import Item

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")


# Establish the mongodb client
def get_mongo_client():
    client = AsyncIOMotorClient(MONGODB_URL)
    return client


# Get the
def get_db_from_mongo_client(mongo_client: AsyncIOMotorClientSession, db_name: str):
    db = mongo_client.get_database(db_name)
    return db


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

    # return the JSONResponse object
    return JSONResponse(content=content, status_code=status_code)


# Convert the item.redis_id from given str type to bson Binary to insert into db with validation rule
def convert_to_bson_binary(item: Item):
    item_dict = item.model_dump(by_alias=True)

    item_dict["redis_id"] = Binary(UUID(item.redis_id).bytes, UUID_SUBTYPE)

    return item_dict
