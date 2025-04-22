from sqlalchemy import (Column, Integer, String,
                        ForeignKey, DateTime, Float,
                        UniqueConstraint, Boolean)
from sqlalchemy.orm import relationship
from src.database.database import Base
from datetime import datetime, timezone

'''
users
-----
id (primary key)
auth_id (from Auth0)
email
phone_number
signup_date
'''
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    auth_id = Column(String, index=True, unique=True,nullable=False)
    email = Column(String)
    phone_number = Column(String)
    signup_date = Column(DateTime, default=datetime.now(timezone.utc))
    riot_profiles = relationship("RiotProfile", back_populates="users")

'''
riot_profiles
-------------
id (primary key)
user_id (foreign key to users.id)
game_name
tag_line
region
last_checked
'''
class RiotProfile(Base):
    __tablename__ = "riot_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    game_name = Column(String)
    tagline = Column(String)
    region = Column(String)
    last_checked = Column(DateTime, default=datetime.now(timezone.utc))
    active = Column(Boolean, default=True)
    kda_logs = relationship("KDALog", back_populates="riot_profiles")
    users = relationship("User", back_populates="riot_profiles")
'''
id (PK)
riot_profile_id (FK)
match_id
kills
deaths
assists
kda_ratio
timestamp
'''
class KDALog(Base):
    __tablename__ = "kda_logs"

    id = Column(Integer, primary_key=True)
    riot_profile_id = Column(Integer, ForeignKey("riot_profiles.id"), index=True)
    match_id = Column(String)
    kda_ratio = Column(Float)
    timestamp = Column(DateTime)
    '''
    __table_args__ = (
        UniqueConstraint('match_id', 'riot_profile_id', name='uq_match_profile'),
    )
    '''
    riot_profiles = relationship("RiotProfile", back_populates="kda_logs")
