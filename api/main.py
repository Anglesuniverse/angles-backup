from fastapi import FastAPI, HTTPException
from typing import List
import json, os
from datetime import datetime
from db import get_conn
from models import (
    VaultIngest, VaultQuery,
    DecisionCreate, DecisionRecommend, DecisionStatusUpdate
)

app = FastAPI(title="Angles OS API")

@app.get("/health")
def health():
    return {"status": "OK"}

# --- Vault ---
@app.post("/vault/ingest")
def vault_ingest(data: VaultIngest):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO vault (source, chunk, summary, links) VALUES (%s,%s,%s,%s)",
        (data.source, data.chunk, data.summary, data.links)
    )
    conn.commit(); cur.close(); conn.close()
    return {"status": "ingested"}

@app.post("/vault/query")
def vault_query(data: VaultQuery):
    # Placeholder: naive fetch (upgrade to pgvector later)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT source, summary FROM vault ORDER BY created_at DESC LIMIT %s", (data.top_k,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"results": [{"source": r[0], "summary": r[1]} for r in rows]}

# --- Decisions ---
@app.post("/decisions")
def create_decision(payload: DecisionCreate):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO fastapi_decisions (topic, options, status) VALUES (%s,%s,'open') RETURNING id",
        (payload.topic, json.dumps([o.model_dump() for o in payload.options]))
    )
    new_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "status": "open"}

@app.get("/decisions")
def list_decisions(status: str = "open"):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, topic, options, status, created_at FROM fastapi_decisions WHERE status=%s ORDER BY created_at DESC", (status,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{
        "id": r[0], "topic": r[1], "options": r[2],
        "status": r[3], "created_at": r[4].isoformat()
    } for r in rows]

@app.get("/decisions/{did}")
def get_decision(did: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, topic, options, chosen, rationale, status, created_at, updated_at FROM fastapi_decisions WHERE id=%s", (did,))
    r = cur.fetchone()
    cur.close(); conn.close()
    if not r: raise HTTPException(404, "Not found")
    return {
        "id": r[0], "topic": r[1], "options": r[2], "chosen": r[3],
        "rationale": r[4], "status": r[5],
        "created_at": r[6].isoformat(), "updated_at": r[7].isoformat()
    }

@app.post("/decisions/{did}/recommend")
def recommend_decision(did: int, payload: DecisionRecommend):
    # Minimal recommender: pick option with shortest cons / longest pros as heuristic
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT options FROM fastapi_decisions WHERE id=%s", (did,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        raise HTTPException(404, "Not found")
    options = row[0]
    best = None
    best_score = -1e9
    for opt in options:
        score = len(opt.get("pros", [])) - len(opt.get("cons", []))
        if score > best_score:
            best_score = score; best = opt["option"]
    rationale = payload.rationale or f"Chosen by heuristic: pros - cons = {best_score}"
    cur.execute(
        "UPDATE fastapi_decisions SET chosen=%s, rationale=%s, updated_at=%s WHERE id=%s",
        (best, rationale, datetime.utcnow(), did)
    )
    conn.commit(); cur.close(); conn.close()
    return {"id": did, "chosen": best, "rationale": rationale}

@app.post("/decisions/{did}/approve")
def approve_decision(did: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE fastapi_decisions SET status='approved', updated_at=%s WHERE id=%s", (datetime.utcnow(), did))
    conn.commit(); cur.close(); conn.close()
    return {"id": did, "status": "approved"}

@app.post("/decisions/{did}/decline")
def decline_decision(did: int, payload: DecisionStatusUpdate):
    if payload.status not in ("declined",):
        raise HTTPException(400, "Use status='declined'")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE fastapi_decisions SET status='declined', updated_at=%s WHERE id=%s", (datetime.utcnow(), did))
    conn.commit(); cur.close(); conn.close()
    return {"id": did, "status": "declined"}