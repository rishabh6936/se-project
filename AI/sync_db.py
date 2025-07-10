# You could place this in a file like Common/db_sync.py
import pymongo
from typing import Optional
from datetime import datetime
import logging

# Set up logging for this module
logger = logging.getLogger(__name__)

class SyncDatabase:
    """
    A synchronous database connection class for the worker.
    It uses the 'pymongo' driver for standard, blocking database operations.
    """
    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        """
        Initializes the synchronous connection to the MongoDB database.
        
        Args:
            connection_string (str): The MongoDB connection URL.
        """
        try:
            self.client = pymongo.MongoClient(connection_string)
            # The 'text_db' and 'texts' names should match what the async part uses
            self.db = self.client["text_db"]
            self.collection = self.db["texts"]
            # Ping the server to confirm a successful connection.
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB (sync client).")
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB (sync client): {e}")
            raise

    def create_text_sync(self, content: str, topic: Optional[str] = None) -> str:
        """
        Creates a new text document in the 'texts' collection synchronously.
        This is the primary method used by the worker after analyzing a text.

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
            result = self.collection.insert_one(doc)
            inserted_id = str(result.inserted_id)
            logger.info(f"Document inserted with ID: {inserted_id}")
            return inserted_id
        except Exception as e:
            logger.error(f"Failed to insert document into database: {e}")
            # Re-raise the exception so the calling code in the worker knows it failed
            raise

    def close_connection(self):
        """
        Closes the synchronous database connection.
        Good practice to call this on graceful shutdown of the worker.
        """
        self.client.close()
        logger.info("MongoDB synchronous connection closed.")