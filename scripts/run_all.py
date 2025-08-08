import os, subprocess, sys, json, random
MAX_TRIES=int(os.getenv("MAX_AUTOFIX_ATTEMPTS","3"))

def run(cmd):
    print(f"→ {cmd}")
    return subprocess.run(cmd, shell=True).returncode

def self_check():  return run("python tools/self_check.py")
def autofix():     return run("python tools/autofix.py")
def memsync_bg():  return subprocess.Popen([sys.executable,"memory/memory_sync.py"])
def notion_sync(): return run("python tools/notion_sync.py")
def gh_backup():   return run("python tools/github_backup.py")

def loop_until_green():
    tries=0
    while tries<MAX_TRIES:
        if self_check()==0:
            print("✅ All checks green."); return True
        print("⚠ Self-check failed → AutoFix…"); autofix(); tries+=1
    return False

def post_run_verify():
    # lightweight verification: try MemorySync once, optional Notion, optional GitHub
    rc = run("python memory/memory_sync.py & sleep 1; pkill -f memory_sync.py || true")
    print("MemSync test rc:", rc)
    if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
        notion_sync()
    if os.getenv("GITHUB_TOKEN") and os.getenv("GITHUB_REPO"):
        gh_backup()
    print("✅ Post-run verify complete.")

if __name__=="__main__":
    ok = loop_until_green()
    if not ok:
        print("❌ Still failing. Open Supabase → SQL Editor → run migrations/ensure_schema.sql, then re-run: python scripts/run_all.py")
        sys.exit(1)
    memsync_bg()
    post_run_verify()
    print("🚀 Backend services running. Cost-safe model in use. Set OPENAI_MODEL=gpt-5 to upscale when needed.")
