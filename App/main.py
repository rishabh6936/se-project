from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import uvicorn
from .db import Database
from .cache import Cache
from .data import *
import os

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
cache = Cache(os.getenv("REDIS_URL", "redis://localhost:6379"))

def get_database():
    return db

def get_cache():
    return cache

@app.get("/stats", response_model=StatsResponse)
async def get_stats(cache_inst: Cache = Depends(get_cache), db_inst: Database = Depends(get_database)):
    """
    Get latest statistics from database (number of texts).
    First checks cache, then database if cache miss.
    """
    try:
        cached_stats = cache_inst.get_stats()
        if cached_stats:
            return cached_stats
        
        total_texts = db_inst.get_text_count()
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
        texts = db_inst.get_texts_by_topic(topic)
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
        
        texts = db_inst.get_texts_by_time_period(start_date, end_date)
        return texts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving texts by period: {str(e)}")

@app.post("/texts", response_model=TextResponse)
async def create_text(text_data: TextCreate, db_inst: Database = Depends(get_database)):
    """
    Create a new short text. Timestamp is automatically set.
    """
    try:
        if not text_data.content.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")
        
        created_text = db_inst.create_text(
            content=text_data.content,
            topic=text_data.topic
        )
        return created_text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating text: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)