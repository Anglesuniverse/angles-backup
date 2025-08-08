import os, sys, json
from supabase import create_client, Client

REQUIRED_ENV = ["SUPABASE_URL","SUPABASE_ANON_KEY","OPENAI_API_KEY","OPENAI_MODEL"]
REQUIRED_TABLES = {
  "decision_vault": ["id","category","status","content","date_added","last_updated","tags","notion_synced"],
  "system_logs": ["id","level","message","ts"],
  "file_snapshots": ["id","file_path","content","ts"],
  "run_artifacts": ["id","artifact_name","artifact_type","ts"]
}

def env_check():
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    return {"name":"env_check","ok": len(missing)==0, "missing":missing}

def supabase_client():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def table_exists(sb: Client, t: str) -> bool:
    try:
        sb.table(t).select("id").limit(1).execute(); return True
    except Exception: return False

def columns_ok(sb: Client, t: str, cols: list) -> bool:
    try:
        res = sb.table(t).select("*").limit(1).execute()
        if res.data:
            have=set(res.data[0].keys()); return all(c in have for c in cols)
        return True
    except Exception: return False

def supabase_schema_check():
    sb = supabase_client()
    res={}
    for t,cols in REQUIRED_TABLES.items():
        ex = table_exists(sb,t)
        res[t]={"exists":ex,"columns_ok": (columns_ok(sb,t,cols) if ex else False)}
    ok = all(v["exists"] and v["columns_ok"] for v in res.values())
    return {"name":"supabase_schema","ok":ok,"details":res}

def openai_check():
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini")
        r=openai.chat.completions.create(
            model=model,
            messages=[{"role":"user","content":"OK"}],
            max_tokens=2, temperature=0
        )
        content=r.choices[0].message.content.strip().upper()
        return {"name":"openai_check","ok": content=="OK","model":model}
    except Exception as e:
        return {"name":"openai_check","ok":False,"error":str(e)}

def notion_check():
    if not os.getenv("NOTION_API_KEY") or not os.getenv("NOTION_DATABASE_ID"):
        return {"name":"notion_check","ok":True,"skipped":True}
    import requests
    headers={"Authorization":f"Bearer {os.getenv('NOTION_API_KEY')}",
             "Notion-Version":"2022-06-28","Content-Type":"application/json"}
    url=f"https://api.notion.com/v1/databases/{os.getenv('NOTION_DATABASE_ID')}"
    try:
        r=requests.get(url, headers=headers, timeout=10)
        return {"name":"notion_check","ok":r.status_code==200,"status":r.status_code}
    except Exception as e:
        return {"name":"notion_check","ok":False,"error":str(e)}

def run_self_check():
    checks=[env_check(), supabase_schema_check(), openai_check(), notion_check()]
    all_ok=all(c.get("ok") for c in checks)
    print(json.dumps({"all_ok":all_ok,"checks":checks}, indent=2))
    return all_ok

if __name__=="__main__":
    sys.exit(0 if run_self_check() else 1)
