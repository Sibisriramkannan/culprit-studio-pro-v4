import sqlite3, json
from pathlib import Path
from datetime import datetime
from app.config import settings

DB_PATH = Path(settings.DATA_DIR) / "culprit.db"

def conn():
    c=sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS jobs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      job_id TEXT UNIQUE,
      mode TEXT,
      title TEXT,
      status TEXT,
      stage TEXT,
      progress INTEGER DEFAULT 0,
      video_path TEXT,
      youtube_video_id TEXT,
      created_at TEXT,
      completed_at TEXT,
      error TEXT,
      config_json TEXT
    );
    CREATE TABLE IF NOT EXISTS schedules(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT,
      enabled INTEGER DEFAULT 1,
      preset TEXT,
      local_time TEXT,
      second_local_time TEXT,
      weekday INTEGER DEFAULT 0,
      custom_cron TEXT,
      config_json TEXT,
      created_at TEXT,
      last_run TEXT,
      next_run TEXT,
      last_status TEXT
    );
    CREATE TABLE IF NOT EXISTS settings_kv(
      key TEXT PRIMARY KEY,
      value TEXT
    );
    """)
    c.commit(); c.close()

def insert_job(job_id, mode, title, config):
    c=conn()
    c.execute("INSERT INTO jobs(job_id,mode,title,status,stage,progress,created_at,config_json) VALUES(?,?,?,?,?,?,?,?)",
              (job_id,mode,title,"queued","queued",0,datetime.now().isoformat(),json.dumps(config)))
    c.commit(); c.close()

def update_job(job_id, **kw):
    if not kw:return
    c=conn()
    cols=", ".join(f"{k}=?" for k in kw)
    c.execute(f"UPDATE jobs SET {cols} WHERE job_id=?", (*kw.values(), job_id))
    c.commit(); c.close()

def list_jobs(limit=100):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?",(limit,)).fetchall()]; c.close(); return rows

def stats():
    c=conn()
    total=c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    done=c.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0]
    failed=c.execute("SELECT COUNT(*) FROM jobs WHERE status='failed'").fetchone()[0]
    queued=c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]
    c.close()
    return {"total":total,"completed":done,"failed":failed,"active":queued}
