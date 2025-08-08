import os, glob, time
from datetime import datetime
import schedule
from supabase import create_client

LOG_LEVEL=os.getenv("LOG_LEVEL","INFO")
INTERVAL=int(os.getenv("SYNC_INTERVAL_MINUTES","30"))
sb=create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def log(level,msg):
    if LOG_LEVEL in ("INFO","DEBUG") or level=="ERROR":
        print(f"[{datetime.utcnow().isoformat()}Z] {level} | {msg}")

def snapshot_files():
    for path in glob.glob("**/*.py", recursive=True):
        try:
            with open(path,"r",encoding="utf-8") as f: content=f.read()
            sb.table("file_snapshots").insert({"file_path":path,"content":content}).execute()
        except Exception as e:
            log("ERROR", f"snapshot failed {path}: {e}")

def run_once():
    log("INFO","MemorySync tick"); snapshot_files()

if __name__=="__main__":
    run_once()
    schedule.every(INTERVAL).minutes.do(run_once)
    log("INFO", f"MemorySync scheduled every {INTERVAL} minutes")
    while True:
        schedule.run_pending(); time.sleep(1)
