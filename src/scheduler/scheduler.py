from apscheduler.schedulers.background import BackgroundScheduler
from src.database.database import SessionLocal
from src.database import models
from src.database.kda_helper import update_kda_log_for_profile, build_league_of_graphs_url
from messaging.message import send_message
import os
from dotenv import load_dotenv

scheduler = BackgroundScheduler()
load_dotenv()

def update_all_active_kda_logs():
    db = SessionLocal()
    try:
        active_profiles = db.query(models.RiotProfile).filter(models.RiotProfile.active == True).all()
        for profile in active_profiles:
            try:
                old_log = profile.kda_logs
                old_kda = old_log.kda_ratio
                new_log = update_kda_log_for_profile(profile, db)
                new_kda = new_log.kda_ratio
                if new_kda != old_kda and new_kda < 1:
                    send_message(from_=os.getenv("TWILIO_MY_NUMBER"),
                                 to=os.getenv("TWILIO_VIRTUAL_NUMBER"),
                                 message=f"{profile.game_name}#{profile.tagline} just went negative. "
                                         f"You can view the match here: "
                                         f"{build_league_of_graphs_url(new_log.match_id)}",
                                 account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
                                 auth_token=os.getenv("TWILIO_AUTH_TOKEN")
                                 )
            except Exception as e:
                print(f"[Scheduler] Failed to update profile {profile.id}: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(update_all_active_kda_logs, 'interval', seconds=10)
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()