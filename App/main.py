from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import uvicorn
import os

from db import Database
from cache import Cache
from queue_manager_enqueue import RedisQueue
from data import *


app = FastAPI(
    title="Text Management API",
    description="API for managing short texts with timestamps",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


db = Database(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
cache = Cache(os.getenv("REDIS_CACHE_URL", "redis://localhost:6379"))
queue = RedisQueue(
    queue_name="text_creation_queue", 
    url=os.getenv("REDIS_QUEUE_URL", "redis://localhost:6379")
)

def get_database():
    return db

def get_cache():
    return cache

def get_queue():
    return queue

# --- Endpoints ---

@app.post("/texts", status_code=status.HTTP_202_ACCEPTED, response_model=JobSubmissionResponse)
async def submit_text_creation(
    text_data: TextCreate, 
    queue_inst: RedisQueue = Depends(get_queue)
):
    """
    Accepts a new text for creation, queues it for background processing.
    This endpoint returns immediately.
    """
    try:
        if not text_data.content.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")
        
        job_payload = text_data.dict()
        
        queue_inst.enqueue(job_payload)
        
        return JobSubmissionResponse(
            message="Your request to create a text has been accepted and is being processed.",
            queue_size=queue_inst.get_size()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting job to queue: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats(cache_inst: Cache = Depends(get_cache), db_inst: Database = Depends(get_database)):
    """
    Get latest statistics from database (number of texts).
    First checks cache, then database if cache miss.
    """
    try:
        cached_stats = await cache_inst.get_stats()
        if cached_stats:
            return cached_stats
        
        total_texts =await db_inst.get_text_count()
        stats = StatsResponse(
            total_texts=total_texts,
            last_updated=datetime.now()
        )
        
        cache_inst.set_stats(stats)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@app.get("/texts/topic/{topic}", response_model=List[TextResponse])
async def get_texts_by_topic(topic: str, db_inst: Database = Depends(get_database)):
    """
    Get short texts related to a specific topic.
    """
    try:
        texts = await db_inst.get_texts_by_topic(topic)
        return texts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving texts by topic: {str(e)}")

@app.get("/texts/period", response_model=List[TextResponse])
async def get_texts_by_period(
    start_date: datetime,
    end_date: datetime,
    db_inst: Database = Depends(get_database)
):
    """
    Get short texts within a specific time period.
    """
    try:
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        texts = await db_inst.get_texts_by_time_period(start_date, end_date)
        return texts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving texts by period: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)