import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.db import conn
from app.pipeline import run

scheduler=BackgroundScheduler()

def _trigger_from_row(row):
    preset=row["preset"]
    if preset=="every_2_hours": return IntervalTrigger(hours=2)
    hh,mm=map(int,row["local_time"].split(":"))
    if preset=="daily": return CronTrigger(hour=hh,minute=mm)
    if preset=="weekly": return CronTrigger(day_of_week=row["weekday"],hour=hh,minute=mm)
    if preset=="custom":
        if not row["custom_cron"]: raise ValueError("custom_cron missing")
        return CronTrigger.from_crontab(row["custom_cron"])
    # twice daily handled as two jobs
    return CronTrigger(hour=hh,minute=mm)

def execute_schedule(schedule_id):
    c=conn();row=c.execute("SELECT * FROM schedules WHERE id=?",(schedule_id,)).fetchone();c.close()
    if not row or not row["enabled"]:return
    try:
        cfg=json.loads(row["config_json"]);run(cfg);status="completed"
    except Exception as e:status=f"failed: {e}"
    c=conn();c.execute("UPDATE schedules SET last_run=?,last_status=? WHERE id=?",(datetime.now().isoformat(),status,schedule_id));c.commit();c.close()

def reload_schedules():
    for j in list(scheduler.get_jobs()):
        if j.id.startswith("sched-"): scheduler.remove_job(j.id)
    c=conn();rows=c.execute("SELECT * FROM schedules WHERE enabled=1").fetchall();c.close()
    for row in rows:
        if row["preset"]=="twice_daily":
            for idx,t in enumerate([row["local_time"],row["second_local_time"] or "20:00"]):
                hh,mm=map(int,t.split(":"))
                scheduler.add_job(execute_schedule,CronTrigger(hour=hh,minute=mm),args=[row["id"]],
                                  id=f"sched-{row['id']}-{idx}",replace_existing=True)
        else:
            scheduler.add_job(execute_schedule,_trigger_from_row(row),args=[row["id"]],
                              id=f"sched-{row['id']}",replace_existing=True)

def start():
    if not scheduler.running:scheduler.start()
    reload_schedules()
