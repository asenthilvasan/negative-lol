from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, timezone
from typing import List, Annotated, Optional
from src.database import models
from src.database.database import engine, SessionLocal
from sqlalchemy.orm import Session
import uuid, os
from src.negative_lol.riot_get_info import get_all_from_names, get_puuid
from dotenv import load_dotenv

app=FastAPI()
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

    if riot_profile not in user.riot_profiles:
        user.riot_profiles.append(riot_profile)
        db.commit()

    return {"id": riot_profile.id, "message": "Riot Profile created"}

@app.post("/kda_logs/create")
async def create_kda_log(log: KDALogCreate, db: db_dependency):

    riot_profile = db.query(models.RiotProfile).filter(models.RiotProfile.id == log.riot_profile_id).first()
    if not riot_profile:
        raise HTTPException(status_code=404, detail="Riot profile not found")

    existing_log = db.query(models.KDALog).filter_by(riot_profile_id=riot_profile.id).first()
    if existing_log:
        raise HTTPException(status_code=400, detail="KDA Log already exists for this profile")

    info = get_all_from_names(riot_profile.game_name,
                              riot_profile.tagline,
                              riot_profile.region,
                              api_key)

    db_kda_log = models.KDALog(match_id=info["match_id"],
                               kda_ratio=info["kda"],
                               timestamp=info["timestamp"],
                               riot_profile_id=riot_profile.id)

    riot_profile.last_checked = datetime.now(timezone.utc)

    db.add(db_kda_log)
    db.commit()
    db.refresh(db_kda_log)

    return {"id": db_kda_log.id, "message": "KDA Log created"}

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

    log = db.query(models.KDALog).filter(models.KDALog.riot_profile_id == log_update.riot_profile_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="Cannot find log - cannot update nonexistent log")

    info = get_all_from_names(riot_profile.game_name, riot_profile.tagline, riot_profile.region, api_key)

    log.match_id = info["match_id"]
    log.kda_ratio = info["kda"]
    log.timestamp = info["timestamp"]

    riot_profile.last_checked = datetime.now(timezone.utc)

    db.commit()
    db.refresh(log)
    return {"id": log.id, "message": "KDA Log updated"}

@app.get("/kda_logs/read/{riot_profile_id}")
async def read_kda_logs(riot_profile_id: int, db: db_dependency):
    result = db.query(models.KDALog).filter(models.KDALog.riot_profile_id == riot_profile_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="KDALog not found")
    return result