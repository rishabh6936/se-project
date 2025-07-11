import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

class Database:
    """
    An asynchronous database connection class.
    """
    def __init__(self, connection_string: str):
        """
        Initializes the async client. Note: Connection is made lazily on first operation.
        """
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        
        self.connection_string = connection_string
        self.client = AsyncIOMotorClient(connection_string)
        
        if "/microservice_db" in connection_string:
            self.db = self.client.microservice_db
        else:
            self.db = self.client.get_default_database()
            
        self.collection = self.db["texts"]
        logger.info(f"AsyncDatabase client initialized with connection: {self._mask_password(connection_string)}")

    def _mask_password(self, connection_string: str) -> str:
        """Mask password in connection string for logging"""
        if "://" in connection_string and "@" in connection_string:
            parts = connection_string.split("://")
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                if "@" in rest:
                    auth_part, host_part = rest.split("@", 1)
                    if ":" in auth_part:
                        user, _ = auth_part.split(":", 1)
                        return f"{protocol}://{user}:***@{host_part}"
        return connection_string

    async def connect_and_ping(self):
        """
        Explicitly connects and pings the server to confirm a successful connection.
        This should be called during application startup.
        """
        try:
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB (async client).")
            
            await self.db.command('ping')
            logger.info(f"Successfully authenticated to database: {self.db.name}")
            
        except Exception as e:
            logger.error(f"Could not connect to MongoDB (async client): {e}")
            raise

    async def create_text_async(self, content: str, topic: Optional[str] = None):
        """
        Creates a new text document in the 'texts' collection asynchronously.
        """
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content must be a non-empty string.")

        doc = {
            "content": content,
            "topic": topic,
            "timestamp": datetime.utcnow()
        }
        
        try:
            result = await self.collection.insert_one(doc)
            inserted_id = str(result.inserted_id)
            logger.info(f"Document inserted with ID: {inserted_id}")
            return inserted_id
        except Exception as e:
            logger.error(f"Failed to insert document into database: {e}")
            raise

    def close_connection(self):
        """
        Closes the asynchronous database connection.
        """
        self.client.close()
        logger.info("MongoDB asynchronous connection closed.")
