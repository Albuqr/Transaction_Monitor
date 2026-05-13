import os
import sys
import sqlite3
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI
import redis

load_dotenv()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=redis_host, port=redis_port, db=redis_db,
                decode_responses=True)


app = FastAPI()

class DecisionModel(BaseModel):
    transaction_id: str
    is_legitimate: bool

@app.get("/alerts")
def get_alerts():
    db_conn = sqlite3.connect("alerts.db")
    db_cursor = db_conn.cursor()
    db_cursor.execute(
        """ select * from alerts where reviewed = 0 """
    )
    results = db_cursor.fetchall()
    return results

@app.post("/resolutions")
def post_resolutions(decision: DecisionModel):
    db_conn = sqlite3.connect("alerts.db")
    db_cursor = db_conn.cursor()
    db_cursor.execute(
        "select cost_center, amount FROM alerts WHERE transaction_id = ?",
        (decision.transaction_id,)
    )
    row = db_cursor.fetchone()

    if not row:
        return {"error": "Transaction not found"}
    cost_center, amount = row

    db_cursor.execute(
        "update alerts set reviewed = 1 where transaction_id = ?",
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