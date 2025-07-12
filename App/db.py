from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime
from data import TextResponse

class Database:
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
    
    async def get_text_count(self) -> int:
        return await self.collection.count_documents({})
    
    async def get_texts_by_topic(self, topic: str) -> List[TextResponse]:
        cursor = self.collection.find({"topic": topic})
        docs = await cursor.to_list(length=20)
        return [self._doc_to_response(doc) for doc in docs]
    
    async def get_texts_by_time_period(self, start_date: datetime, end_date: datetime) -> List[TextResponse]:
        cursor = self.collection.find({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        docs = await cursor.to_list(length=500)
        return [self._doc_to_response(doc) for doc in docs]

    def _doc_to_response(self, doc: dict) -> TextResponse:
        return TextResponse(
            id=str(doc["_id"]),
            content=doc["content"],
            topic=doc.get("topic"),
            timestamp=doc["timestamp"]
        )