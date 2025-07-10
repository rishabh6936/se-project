# You could place this in a file like Common/db_async.py

from motor.motor_asyncio import AsyncIOMotorClient # The async driver
from typing import Optional
from datetime import datetime
import logging
import asyncio

# Set up logging for this module
logger = logging.getLogger(__name__)

class Database:
    """
    An asynchronous database connection class.
    It uses the 'motor' driver for non-blocking database operations suitable for asyncio applications.
    """
    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        """
        Initializes the async client. Note: Connection is made lazily on first operation.
        
        Args:
            connection_string (str): The MongoDB connection URL.
        """
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client["text_db"]
        self.collection = self.db["texts"]
        logger.info("AsyncDatabase client initialized.")

    async def connect_and_ping(self):
        """
        Explicitly connects and pings the server to confirm a successful connection.
        This should be called during application startup.
        """
        try:
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB (async client).")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB (async client): {e}")
            raise

    async def create_text_async(self, content: str, topic: Optional[str] = None) -> str:
        """
        Creates a new text document in the 'texts' collection asynchronously.

        Args:
            content (str): The original text content.
            topic (Optional[str]): The topic identified by the AI model.

        Returns:
            str: The string representation of the new document's ObjectId.
        """
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content must be a non-empty string.")

        doc = {
            "content": content,
            "topic": topic,
            "timestamp": datetime.utcnow()
        }
        
        try:
            # Every database call is now awaited
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


# --- Example of how to use this class ---
async def example_usage():
    """
    Demonstrates how to instantiate and use the AsyncDatabase class.
    """
    # This URL would come from an environment variable in a real app
    MONGO_URL = "mongodb://localhost:27017"
    
    db = AsyncDatabase(MONGO_URL)
    
    try:
        # Check the connection on startup
        await db.connect_and_ping()
        
        # Perform an operation
        new_id = await db.create_text_async(content="This is an async test.", topic="technology")
        print(f"Successfully created document with ID: {new_id}")
        
    finally:
        # Clean up the connection when done
        db.close_connection()

if __name__ == "__main__":
    # To run the example, you use asyncio.run()
    asyncio.run(example_usage())