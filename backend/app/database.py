"""MongoDB asynchronous database connection and collection helpers."""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient

from backend.app.config import settings

logger = logging.getLogger("telecom.database")


class DatabaseManager:
    """Manages Async Motor client connection and database handles."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect_to_database(self) -> None:
        """Initializes connection to MongoDB and creates indexes."""
        try:
            logger.info("Connecting to MongoDB at: %s", settings.MONGODB_URL)
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
            )
            self.db = self.client[settings.DATABASE_NAME]

            # Verify connection
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB database '%s'", settings.DATABASE_NAME)

            # Ensure indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.predictions.create_index("customer_id")
            await self.db.predictions.create_index("created_at")
            await self.db.customers.create_index("customer_id", unique=True)
        except Exception as e:
            logger.error("Failed to connect to MongoDB: %s", e)
            logger.warning("Application will attempt reconnects on demand.")

    async def close_database_connection(self) -> None:
        """Closes the MongoDB client connection."""
        if self.client is not None:
            logger.info("Closing MongoDB connection...")
            self.client.close()
            logger.info("MongoDB connection closed.")


db_manager = DatabaseManager()


def get_database() -> AsyncIOMotorDatabase:
    """Returns active database handle."""
    if db_manager.db is None:
        client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        return client[settings.DATABASE_NAME]
    return db_manager.db


def get_sync_database():
    """Returns synchronous PyMongo database handle for seeding and offline scripts."""
    client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    return client[settings.DATABASE_NAME]
