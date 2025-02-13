import os
from fastapi import FastAPI, Depends, status, Response
from dotenv import load_dotenv
from uuid import UUID
from loguru import logger


from models import Item, Collection
from helpers import (
    get_mongo_client,
    get_db_from_mongo_client,
    send_response,
    convert_to_bson_binary,
)
from redis_pool import RedisPoolProvider

load_dotenv()

app = FastAPI()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/get/items")
async def get_entries(
    collection: Collection,
    response: Response,
    redis_client: RedisPoolProvider = Depends(RedisPoolProvider),
):
    # Should return all entries in 'db_name' db and 'collection_name' collection
    if not collection.redis_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response_data = {
            "message": "POST Unsuccessful - redis_id invalid",
            "status": response.status_code,
        }

        # return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=False,
            redis_client=redis_client,
            redis_key=None,
        )

    # Basic error handling
    if not collection.collection_name:
        response_data = {
            "message": "collection_name not in request JSON",
            "status": status.HTTP_400_BAD_REQUEST,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=True,
            redis_client=redis_client,
            redis_key=f"{UUID(collection.redis_id)}:get:entries",
        )


@app.post("/post/collection")
async def create_collection(
    collection: Collection,
    response: Response,
    redis_client: RedisPoolProvider = Depends(RedisPoolProvider),
):
    """
    Create a collection in a specific db
    """

    # Basic error handling
    if not collection.collection_name:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response_data = {
            "message": "collection_name not in request JSON",
            "status": response.status_code,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=True,
            redis_client=redis_client,
            redis_key=f"{UUID(collection.redis_id)}:post:collection",
        )

    mongo_client = get_mongo_client()
    db_conn = mongo_client.get_database(collection.db_name)

    # TODO: Ensure db_name exists in mongodb
    if db_conn is not None:
        logger.debug(f"CHECK: {db_conn}")
        pass

    try:
        # create the collection
        await db_conn.create_collection(
            f"{collection.collection_name}", check_exists=True
        )

        response.status_code = status.HTTP_201_CREATED
        response_data = {
            "message": "collection successfully created",
            "status": response.status_code,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=True,
            redis_client=redis_client,
            redis_key=f"{UUID(collection.redis_id)}:post:collection",
        )

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response_data = {
            "message": f"failed to create collection with exception: {e}",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=True,
            redis_client=redis_client,
            redis_key=f"{UUID(collection.redis_id)}:post:collection",
        )


@app.post("/post/items")
async def create_item(
    item: Item,
    response: Response,
    redis_client: RedisPoolProvider = Depends(RedisPoolProvider),
):
    """
    Create an item in the specified db and collection
    """

    # get MongoDB client and establish connection with specified db
    db_conn = get_db_from_mongo_client(
        mongo_client=get_mongo_client(), db_name=item.db_name
    )

    if not item.redis_id:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response_data = {
            "message": "POST Unsuccessful - redis_id invalid",
            "status": response.status_code,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=False,
            redis_client=redis_client,
            redis_key=None,
        )

    # item wasn't passed in with collection as a valid param
    if not item.collection_name:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response_data = {
            "message": f"POST Unsuccessful - collection '{item.collection_name}' does not exist",
            "status": response.status_code,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=True,
            redis_client=redis_client,
            redis_key=f"{UUID(item.redis_id)}:post:items",
        )

    # collection doesn't exist
    if item.collection_name not in await db_conn.list_collection_names():
        response.status_code = status.HTTP_404_NOT_FOUND
        response_data = {
            "message": f"POST Unsuccessful - collection '{item.collection_name}' does not exist",
            "status": response.status_code,
        }

        # publish to the redis client and return a JSONObject
        return await send_response(
            content=response_data,
            status_code=response.status_code,
            pub=True,
            redis_client=redis_client,
            redis_key=f"{UUID(item.redis_id)}:post:items",
        )

    # get the collection from MongoDB
    db_collection = db_conn.get_collection(f"{item.collection_name}")

    item_db_insert = convert_to_bson_binary(item)

    # logger.debug(f"MODEL DUMP: {item_db_insert}")

    new_item = await db_collection.insert_one(item_db_insert)

    # find the _id of newly created item
    created_item = await db_collection.find_one({"_id": new_item.inserted_id})

    response.status_code = status.HTTP_201_CREATED
    response_data = {
        "message": f"POST Successful - created entry for item: {item.name} with item_id: {created_item['_id']}",
        "status": response.status_code,
    }

    # publish to the redis client and return a JSONObject
    return await send_response(
        content=response_data,
        status_code=response.status_code,
        pub=True,
        redis_client=redis_client,
        redis_key=f"{UUID(item.redis_id)}:post:items",
    )


# @app.post("/post/items")
# async def create_item(
#     item: Item,
#     response: Response,
#     redis_client: RedisPoolProvider = Depends(RedisPoolProvider),
# ):
#     """
#     Create an item in the specified db and collection
#     """

#     # get MongoDB client and establish connection with specified db
#     db_conn = get_db_from_mongo_client(
#         mongo_client=get_mongo_client(), db_name=item.db_name
#     )

#     if not item.redis_id:
#         response.status_code = status.HTTP_400_BAD_REQUEST
#         response_data = {
#             "message": "POST Unsuccessful - redis_id invalid",
#             "status": response.status_code,
#         }
#         return JSONResponse(content=response_data, status_code=response.status_code)

#     # item wasn't passed in with collection as a valid param
#     if not item.collection_name:
#         response.status_code = status.HTTP_400_BAD_REQUEST
#         response_data = {
#             "message": f"POST Unsuccessful - collection '{item.collection_name}' does not exist",
#             "status": response.status_code,
#         }
#         await publish(
#             redis_client, f"{UUID(item.redis_id)}:post:items", json.dumps(response_data)
#         )
#         return JSONResponse(content=response_data, status_code=response.status_code)

#     # collection doesn't exist
#     if item.collection_name not in await db_conn.list_collection_names():
#         response.status_code = status.HTTP_404_NOT_FOUND
#         response_data = {
#             "message": f"POST Unsuccessful - collection '{item.collection_name}' does not exist",
#             "status": response.status_code,
#         }
#         await publish(
#             redis_client, f"{UUID(item.redis_id)}:post:items", json.dumps(response_data)
#         )

#     # get the collection from MongoDB
#     db_collection = db_conn.get_collection(f"{item.collection_name}")

#     # handle insertion of item into specific collection
#     new_item = await db_collection.insert_one(item.model_dump(by_alias=True))

#     # find the _id of newly created item
#     created_item = await db_collection.find_one({"_id": new_item.inserted_id})

#     response.status_code = status.HTTP_201_CREATED
#     response_data = {
#         "message": f"POST Successful - created entry for item: {item.name} with item_id: {created_item['_id']}",
#         "status": response.status_code,
#     }

#     await publish(
#         redis_client, f"{UUID(item.redis_id)}:post:items", json.dumps(response_data)
#     )

#     return JSONResponse(content=response_data, status_code=response.status_code)
