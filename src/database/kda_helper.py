from datetime import datetime, timezone
from src.database import models
from src.negative_lol.riot_get_info import get_all_from_names
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("RIOT_API_KEY")

def create_kda_log_for_profile(riot_profile: models.RiotProfile, db):
    info = get_all_from_names(
        riot_profile.game_name,
        riot_profile.tagline,
        riot_profile.region,
        api_key
    )

    kda_log = models.KDALog(
        match_id=info["match_id"],
        kda_ratio=info["kda"],
        timestamp=info["timestamp"],
        riot_profile_id=riot_profile.id
    )
    riot_profile.last_checked = datetime.now(timezone.utc)

    db.add(kda_log)
    db.commit()
    db.refresh(kda_log)
    return kda_log

def update_kda_log_for_profile(riot_profile: models.RiotProfile, db):
    info = get_all_from_names(
        riot_profile.game_name,
        riot_profile.tagline,
        riot_profile.region,
        api_key,
    )

    log = db.query(models.KDALog).filter_by(riot_profile_id=riot_profile.id).first()
    if not log:
        raise ValueError("No KDA log exists for this profile")

    log.match_id = info["match_id"]
    log.kda_ratio = info["kda"]
    log.timestamp = info["timestamp"]
    riot_profile.last_checked = datetime.now(timezone.utc)

    db.commit()
    db.refresh(log)
    return log

