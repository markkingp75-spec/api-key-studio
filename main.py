import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from database import get_db, engine, Base, async_session
from models import StudioUser, Post
from browser import automation_worker

app = FastAPI(title="Custom API Key Studio & Social Automation Engine", version="1.0.0")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

MASTER_CREATOR_EMAIL = "your-email@example.com"

class StudioRegisterRequest(BaseModel):
    MASTER_CREATOR_EMAIL = "emmanuelottah173@gmail.com"
    requested_tier: str = Field("free", example="pro")

class PostRequest(BaseModel):
    platform: str = Field(..., example="twitter")
    content: str = Field(..., example="Autonomous AI agent post test.")
    media_url: str | None = Field(None, example="https://example.com/image.png")

async def get_current_user(api_key: str = Security(api_key_header), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudioUser).where(StudioUser.api_key == api_key))
    user = result.scalar_one_or_none()
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key."
        )
    return user

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("shutdown")
async def shutdown_event():
    await automation_worker.close()
    await engine.dispose()

@app.post("/studio/api/v1/register")
async def register_studio_user(payload: StudioRegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudioUser).where(StudioUser.email == payload.email))
    existing = result.scalar_one_or_none()
    
    if existing:
        return {
            "status": "success",
            "message": "Account already exists.",
            "email": existing.email,
            "tier": existing.tier,
            "api_key": existing.api_key
        }
    
    is_master = (payload.email.lower() == MASTER_CREATOR_EMAIL.lower())
    assigned_tier = "pro" if is_master else payload.requested_tier
    
    new_user = StudioUser(
        email=payload.email,
        tier=assigned_tier,
        is_admin=is_master
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "status": "success",
        "message": "API key generated successfully in Studio.",
        "email": new_user.email,
        "tier": new_user.tier,
        "api_key": new_user.api_key
    }

@app.get("/studio/api/v1/verify")
async def verify_studio_key(api_key: str = Security(api_key_header), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudioUser).where(StudioUser.api_key == api_key))
    user = result.scalar_one_or_none()
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key."
        )
    
    return {
        "status": "valid",
        "email": user.email,
        "tier": user.tier,
        "is_admin": user.is_admin
    }

async def background_post_dispatch(post_id: int, platform: str, content: str, media_url: str | None):
    try:
        await automation_worker.execute_post(platform=platform, content=content, media_url=media_url)
        async with async_session() as session:
            async with session.begin():
                db_post = await session.get(Post, post_id)
                if db_post:
                    db_post.status = "published"
                    session.add(db_post)
    except Exception as e:
        async with async_session() as session:
            async with session.begin():
                db_post = await session.get(Post, post_id)
                if db_post:
                    db_post.status = "failed"
                    session.add(db_post)

@app.post("/api/v1/posts/publish")
async def publish_post(
    payload: PostRequest, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db),
    current_user: StudioUser = Depends(get_current_user)
):
    db_post = Post(
        user_id=current_user.id,
        platform=payload.platform,
        content=payload.content,
        media_url=payload.media_url,
        status="pending"
    )
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)

    background_tasks.add_task(
        background_post_dispatch,
        post_id=db_post.id,
        platform=payload.platform,
        content=payload.content,
        media_url=payload.media_url
    )
    return {
        "status": "accepted",
        "post_id": db_post.id,
        "user_email": current_user.email,
        "tier": current_user.tier,
        "message": "Post saved and dispatched to automation queue."
    }

@app.get("/api/v1/agent/status")
async def agent_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    db_healthy = result.scalar() == 1
    return {
        "engine_status": "operational",
        "database_connected": db_healthy
    }