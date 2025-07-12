from pydantic import BaseModel
from typing import Optional
import hashlib
import json
from datetime import datetime, timedelta

# Pydantic models for request/response
class TextCreate(BaseModel):
    content: str
    topic: Optional[str] = None

class TextResponse(BaseModel):
    id: str
    content: str
    topic: Optional[str] = None
    timestamp: datetime

class StatsResponse(BaseModel):
    total_texts: int
    last_updated: datetime

class JobSubmissionResponse(BaseModel):
    message: str
    queue_size: int    
