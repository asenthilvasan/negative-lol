from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Annotated, Optional
from src.database import models
from src.database.database import engine, SessionLocal
from sqlalchemy.orm import Session
import uuid, os
from src.negative_lol.riot_get_info import get_puuid
from dotenv import load_dotenv
from src.database.kda_helper import create_kda_log_for_profile, update_kda_log_for_profile
from scheduler.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    print("Scheduler started")
    yield
    stop_scheduler()

app=FastAPI(lifespan=lifespan)
models.Base.metadata.create_all(bind=engine)

load_dotenv()
api_key = os.getenv('RIOT_API_KEY')

class UserCreate(BaseModel):
    email: Optional[EmailStr]
    phone_number: Optional[str]
    auth_id: Optional[str]

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
    auth_id: str

class RiotProfileSwitchActive(BaseModel):
    id: int

class RiotProfileRead(BaseModel):
    id: int
    game_name: str
    tagline: str
    region: str
    active: bool
    last_checked: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class KDALogCreate(BaseModel):
    riot_profile_id: int

class KDALogUpdate(BaseModel):
    riot_profile_id: int

class KDALogRead(BaseModel):
    id: int
    match_id: str
    kda_ratio: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


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
    return {"id": db_user.id, "message": "User created"}

@app.post("/riot_profile/create")
async def create_riot_profile(profile: RiotProfileCreate, db: db_dependency):
    user = db.query(models.User).filter(models.User.auth_id == profile.auth_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Authorization not found")

    try:
        profile_puuid = get_puuid(profile.game_name, profile.tagline, profile.region, api_key)
    except:
        raise HTTPException(status_code=404, detail="Cannot find Riot Profile")

    riot_profile = db.query(models.RiotProfile).filter(models.RiotProfile.puuid == profile_puuid).first()
    if not riot_profile:
        riot_profile = models.RiotProfile(
            game_name=profile.game_name,
            tagline=profile.tagline,
            region=profile.region,
            puuid=profile_puuid,
        )
        db.add(riot_profile)
        db.commit()
        db.refresh(riot_profile)
    else:
        raise HTTPException(status_code=400, detail="There already exists a Riot Profile with that info")

    if riot_profile not in user.riot_profiles:
        user.riot_profiles.append(riot_profile)
        db.commit()

    create_kda_log_for_profile(riot_profile=riot_profile, db=db)

    return {"id": riot_profile.id, "message": "Riot Profile created"}

@app.put("/riot_profile/switch_active")
async def switch_active(profile: RiotProfileSwitchActive, db: db_dependency):
    riot_profile = db.query(models.RiotProfile).filter(models.RiotProfile.id == profile.id).first()
    if not riot_profile:
        raise HTTPException(status_code=404, detail="Cannot find Riot Profile")

    if riot_profile.active:
        riot_profile.active = False
    else:
        riot_profile.active = True

    db.commit()
    db.refresh(riot_profile)

    return {"id": riot_profile.id, "message": "Riot Profile active switched"}


@app.post("/kda_logs/create")
async def create_kda_log(log: KDALogCreate, db: db_dependency):
    riot_profile = db.query(models.RiotProfile).filter(models.RiotProfile.id == log.riot_profile_id).first()
    if not riot_profile:
        raise HTTPException(status_code=404, detail="Riot profile not found")

    existing_log = db.query(models.KDALog).filter_by(riot_profile_id=riot_profile.id).first()
    if existing_log:
        raise HTTPException(status_code=400, detail="KDA Log already exists for this profile")

    kda_log = create_kda_log_for_profile(riot_profile, db)

    return {"id": kda_log.id, "message": "KDA Log created"}

'''
active_profiles = db.query(RiotProfile).filter(RiotProfile.active == True).all()

for profile in active_profiles:
    update_kda_log(profile.kda_log.id)
'''
@app.put("/kda_logs/update")
async def update_kda_log(log_update: KDALogUpdate, db: db_dependency):
    # we are given riot_profile_id
    riot_profile = db.query(models.RiotProfile).filter(models.RiotProfile.id == log_update.riot_profile_id).first()
    if not riot_profile:
        raise HTTPException(status_code=404, detail="Riot profile not found")

    try:
        log = update_kda_log_for_profile(riot_profile, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"id": log.id, "message": "KDA Log updated"}

@app.get("/kda_logs/read/{riot_profile_id}")
async def read_kda_logs(riot_profile_id: int, db: db_dependency):
    result = db.query(models.KDALog).filter(models.KDALog.riot_profile_id == riot_profile_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="KDALog not found")
    return result