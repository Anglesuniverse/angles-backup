import os, requests
from supabase import create_client
API=os.getenv("NOTION_API_KEY"); DB=os.getenv("NOTION_DATABASE_ID")
if not (API and DB):
    print("Notion sync skipped (no API/DB)."); raise SystemExit(0)

H={"Authorization":f"Bearer {API}","Notion-Version":"2022-06-28","Content-Type":"application/json"}
sb=create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def push(dec):
    data={"parent":{"database_id":DB},
          "properties":{
            "message":{"title":[{"text":{"content":dec['content'][:2000]}}]},
            "date":{"date":{"start": dec.get("date_added","")}},
            "tag":{"multi_select":[{"name":t} for t in (dec.get("tags") or [])]}
          }}
    r=requests.post("https://api.notion.com/v1/pages", headers=H, json=data)
    return r.status_code==200

def sync():
    rows=sb.table("decision_vault").select("*").eq("notion_synced",False).limit(50).execute().data
    for d in rows:
        if push(d):
            sb.table("decision_vault").update({"notion_synced":True}).eq("id",d["id"]).execute()
            print(f"✅ Notion synced: {d['id']}")

if __name__=="__main__":
    sync()
