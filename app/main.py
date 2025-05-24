from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import httpx
from typing import List, Optional
import json
import os
from datetime import datetime
import random
import asyncio

from app.database import get_db, engine
from app.models import User, Base

app = FastAPI(title="Random Users API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
    conn.commit()

Base.metadata.create_all(bind=engine)

RANDOM_USER_API = "https://randomuser.me/api/"
INITIAL_USERS_COUNT = 1000


async def fetch_users(count: int) -> List[dict]:
    """Асинхронно загружает пользователей с randomuser.me"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RANDOM_USER_API}?results={count}")
        return response.json()["results"]


def process_user_data(user_data: dict) -> dict:
    """Обрабатывает данные пользователя из API"""
    return {
        "gender": user_data["gender"],
        "first_name": user_data["name"]["first"],
        "last_name": user_data["name"]["last"],
        "phone": user_data["phone"],
        "email": user_data["email"],
        "location": {
            "street": user_data["location"]["street"],
            "city": user_data["location"]["city"],
            "state": user_data["location"]["state"],
            "country": user_data["location"]["country"],
            "postcode": user_data["location"]["postcode"],
            "coordinates": user_data["location"]["coordinates"],
            "timezone": user_data["location"]["timezone"]
        },
        "picture": user_data["picture"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@app.on_event("startup")
async def startup_event():
    """Загружает начальные данные при запуске приложения"""
    print("Starting application...")
    db = next(get_db())
    try:
        user_count = db.query(User).count()
        print(f"Current user count: {user_count}")
        
        if user_count == 0:
            print("No users found, loading initial data...")
            users_data = await fetch_users(1000)
            print(f"Fetched {len(users_data)} users from API")
            
            for user_data in users_data:
                processed_user = process_user_data(user_data)
                user = User(**processed_user)
                db.add(user)
                db.flush()
            
            db.commit()
            print(f"Successfully added users to database")
            
            final_count = db.query(User).count()
            print(f"Final user count: {final_count}")
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        db.rollback()
    finally:
        db.close()
        print("Startup completed")


@app.get("/")
async def read_root():
    """Возвращает главную страницу"""
    return FileResponse("static/index.html")


@app.get("/random")
async def read_random_user_page():
    """Возвращает страницу со случайным пользователем"""
    return FileResponse("static/user.html")


@app.get("/{user_id}")
async def read_user(user_id: int, db: Session = Depends(get_db)):
    """Возвращает страницу с информацией о конкретном пользователе"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return FileResponse("static/user.html")


@app.get("/api/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Получает список пользователей с пагинацией"""
    total = db.query(func.count(User.id)).scalar()
    users = db.query(User).offset(skip).limit(limit).all()
    return {
        "total": total,
        "users": users
    }


@app.get("/api/user/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получает информацию о конкретном пользователе"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/random")
async def get_random_user(db: Session = Depends(get_db)):
    """Получает случайного пользователя"""
    total = db.query(func.count(User.id)).scalar()
    if total == 0:
        raise HTTPException(status_code=404, detail="No users found")
    random_id = random.randint(1, total)
    user = db.query(User).filter(User.id == random_id).first()
    return user 