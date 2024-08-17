from os import getenv

from dotenv import load_dotenv
from motor import motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

load_dotenv()


def get_db() -> AsyncIOMotorDatabase:
    """
    Return the database connection
    """

    db_url = getenv("MONGO_URI")
    client = motor_asyncio.AsyncIOMotorClient(db_url, serverSelectionTimeoutMS=10 * 1000)
    db = client[getenv("MONGO_DB_NAME")]

    return db
