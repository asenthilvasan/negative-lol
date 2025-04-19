from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, timedelta,date,time
from typing import List, Annotated, Optional
from src.database import models
from src.database.database import engine, SessionLocal
from sqlalchemy.orm import Session
import uuid

app=FastAPI()
models.Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    email: Optional[EmailStr]
    phone_number: Optional[str]

class UserRead(BaseModel):
    id: int
    email: Optional[EmailStr]
    phone_number: Optional[str]
    signup_date: datetime

    model_config = ConfigDict(from_attributes=True)

class RiotProfileCreate(BaseModel):
    game_name: str
    tagline: str
    region: str

class RiotProfileRead(BaseModel):
    id: int
    game_name: str
    tagline: str
    region: str
    last_checked: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class KDALogCreate(BaseModel):
    match_id: str
    kda_ratio: float
    timestamp: datetime

class KDALogRead(BaseModel):
    id: int
    match_id: str
    kda_ratio: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class RiotProfileWithLogs(RiotProfileRead):
    kda_logs: List[KDALogRead] = []


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/user/create")
async def create_user(user: UserCreate, db: db_dependency):
    db_user = models.User(email=user.email, phone_number=user.phone_number, auth_id=str(uuid.uuid4()))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

@app.post("/riot_profile/create")
async def create_riot_profile(profile: RiotProfileCreate, db: db_dependency):
    db_riot_profile = models.RiotProfile(game_name=profile.game_name,tagline=profile.tagline,region=profile.region)
    db.add(db_riot_profile)
    db.commit()
    db.refresh(db_riot_profile)

@app.post("/kda_logs/create")
async def create_kda_log(log: KDALogCreate, db: db_dependency):
    db_kda_log = models.KDALog(match_id=log.match_id,kda_ratio=log.kda_ratio,timestamp=log.timestamp)
    db.add(db_kda_log)
    db.commit()
    db.refresh(db_kda_log)

@app.get("/kda_logs/read/{riot_profile_id}")
async def read_kda_logs(riot_profile_id: int, db: db_dependency):
    result = db.query(models.KDALog).filter(models.KDALog.riot_profile_id == riot_profile_id).all()
    if not result:
        raise HTTPException(status_code=404, detail="KDALog not found")
    return result