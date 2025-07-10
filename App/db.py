from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime
from data import TextResponse

class Database:
    def __init__(self, connection_string: str = "mongodb://localhost:27017"):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client["text_db"]
        self.collection = self.db["texts"]
    
    async def get_text_count(self) -> int:
        return await self.collection.count_documents({})
    
    async def get_texts_by_topic(self, topic: str) -> List[TextResponse]:
        cursor = self.collection.find({"topic": topic})
        docs = await cursor.to_list(length=20)
        return [self._doc_to_response(doc) for doc in docs]
    
    async def get_texts_by_time_period(self, start_date: datetime, end_date: datetime) -> List[TextResponse]:
        # Return texts within time period
        cursor = self.collection.find({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        docs = await cursor.to_list(length=500)
        return [self._doc_to_response(doc) for doc in docs]
    
    async def create_text(self, content: str, topic: Optional[str] = None) -> TextResponse:
        # Create new text with timestamp and return created object
        doc = {
            "text": content,
            "topic": topic,
            "timestamp": datetime.now().timestamp()
        }
        await self.collection.insert_one(doc)
        return self._doc_to_response(doc)

    def _doc_to_response(self, doc: dict) -> TextResponse:
        # Convert MongoDB document to a TextResponse model
        return TextResponse(
            id=str(doc["_id"]),
            content=doc["text"],
            topic=doc.get("topic"),
            timestamp=doc["timestamp"]
        )