FROM python:3.11-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY / ./
#COPY init-mongo.js ./

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /code
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
    
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
