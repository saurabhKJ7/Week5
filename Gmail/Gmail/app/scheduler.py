from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from .responder import AutoResponder


def start_scheduler() -> BackgroundScheduler:
    responder = AutoResponder()
    scheduler = BackgroundScheduler()
    scheduler.add_job(responder.process_unread_emails, "interval", minutes=5)
    scheduler.start()
    return scheduler 