import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")


def get_mongo_client():
    client = AsyncIOMotorClient(MONGODB_URL)
    return client


def get_db_from_mongo_client(mongo_client: AsyncIOMotorClientSession, db_name: str):
    db = mongo_client.get_database(db_name)
    return db
