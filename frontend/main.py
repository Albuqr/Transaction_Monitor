import os
import sys
import sqlite3
from typing import Annotated
from pydantic import BaseModel, StringConstraints
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis

load_dotenv()

_kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
_redis_host = os.getenv("REDIS_HOST")
if not _redis_host:
    sys.exit("ERROR: REDIS_HOST environment variable is required")

redis_host = _redis_host
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=redis_host, port=redis_port, db=redis_db,
                decode_responses=True)

app = FastAPI()

_allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class DecisionModel(BaseModel):
    transaction_id: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    is_legitimate: bool


@app.get("/alerts")
def get_alerts():
    db_conn = sqlite3.connect("alerts.db")
    db_conn.row_factory = sqlite3.Row
    db_cursor = db_conn.cursor()
    db_cursor.execute("SELECT * FROM alerts")
    results = db_cursor.fetchall()
    return [dict(row) for row in results]


@app.post("/resolutions")
def post_resolutions(decision: DecisionModel):
    db_conn = sqlite3.connect("alerts.db")
    db_cursor = db_conn.cursor()
    db_cursor.execute(
        "SELECT cost_center, amount FROM alerts WHERE transaction_id = ?",
        (decision.transaction_id,)
    )
    row = db_cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
    cost_center, amount = row

    db_cursor.execute(
        "UPDATE alerts SET reviewed = 1 WHERE transaction_id = ?",
        (decision.transaction_id,)
    )
    db_conn.commit()

    if decision.is_legitimate:
        baseline_key = f"baseline:{cost_center}"
        baseline_data = r.hgetall(baseline_key)

        if baseline_data:
            old_count = int(baseline_data.get("count", 0))
            old_sum = float(baseline_data.get("sum", 0))

            new_count = old_count + 1
            new_sum = old_sum + amount
            new_mean = new_sum / new_count

            r.hset(baseline_key, mapping={
                "count": new_count,
                "sum": new_sum,
                "mean": new_mean
            })
            return {"status": "resolved", "action": "baseline updated"}
    return {"status": "resolved", "action": "marked as not legitimate or fraud - no baseline update"}