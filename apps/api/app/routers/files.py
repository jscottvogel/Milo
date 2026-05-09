import logging
import os
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

import boto3

from app.middleware.auth import AuthMiddleware, RequestContext
from db.models.memory import MemoryChunk
from agent.llm.bedrock import BedrockClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/files", tags=["Files"])


@router.post("/check-duplicate")
async def check_duplicate(request: Request):
    """
    Check if a file with the given name has already been ingested into memory.
    """
    data = await request.json()
    filename = data.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")
        
    context: RequestContext = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Unauthorized")
    tenant_id = str(context.tenant_id)
        
    # We query the MemoryChunk table directly to see if a metadata 'source_file' matches
    # Since metadata is JSONB, we can use the @> operator or just search it
    # We'll use Bedrock semantic search with the filename to see if we have high confidence matches,
    # or just query the DB. It's safer to query the DB JSONB.
    
    # Actually, SQLAlchemy JSONB querying can be complex. Let's just do a vector search on the filename.
    bedrock = BedrockClient()
    query_embedding = await bedrock.embed_text(filename)
    
    db = getattr(request.state, "db", None)
    if not db:
        raise HTTPException(status_code=500, detail="Database session not found")
    stmt = select(MemoryChunk).where(
        MemoryChunk.tenant_id == uuid.UUID(tenant_id)
    ).order_by(MemoryChunk.embedding.cosine_distance(query_embedding)).limit(5)
    
    chunks = db.scalars(stmt).all()
    
    for chunk in chunks:
        if chunk.metadata_jsonb and chunk.metadata_jsonb.get("source_file") == filename:
            return {"exists": True, "message": "File has already been uploaded."}
            
    return {"exists": False}


@router.post("/upload")
async def upload_files(request: Request, files: list[UploadFile] = File(...)):
    """
    Upload one or more files to S3.
    """
    context: RequestContext = getattr(request.state, "auth_context", None)
    if not context:
        raise HTTPException(status_code=401, detail="Unauthorized")
    tenant_id = str(context.tenant_id)

    bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
    s3 = boto3.client("s3")
    
    total_size = 0
    uploaded_paths = []
    
    for file in files:
        # Check size limit per file (25MB)
        # Note: FastAPI doesn't easily expose size before reading, so we read chunks
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File {file.filename} exceeds 25MB limit")
            
        total_size += size
        
    if total_size > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Total batch size exceeds 100MB limit")
        
    # Mock ClamAV malware scan
    await asyncio.sleep(1)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    for file in files:
        safe_filename = file.filename.replace(" ", "_")
        key = f"{tenant_id}/uploads/{date_str}/{safe_filename}"
        
        # Upload to S3
        loop = asyncio.get_running_loop()
        file_content = await file.read()
        await loop.run_in_executor(
            None, 
            lambda: s3.put_object(Bucket=bucket, Key=key, Body=file_content)
        )
        
        uploaded_paths.append(f"uploads/{date_str}/{safe_filename}")
        
    return {"paths": uploaded_paths}
