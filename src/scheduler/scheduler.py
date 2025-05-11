import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from src.database.database import SessionLocal
from src.database import models
from src.database.kda_helper import update_kda_log_for_profile

scheduler = BackgroundScheduler()

def update_all_active_kda_logs():
    db = SessionLocal()
    try:
        active_profiles = db.query(models.RiotProfile).filter(models.RiotProfile.active == True).all()
        for profile in active_profiles:
            try:
                update_kda_log_for_profile(profile, db)
            except Exception as e:
                print(f"[Scheduler] Failed to update profile {profile.id}: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(update_all_active_kda_logs, 'interval', minutes=10)
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()