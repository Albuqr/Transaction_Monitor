import os
import sys
from google.cloud import bigquery
import redis
from dotenv import load_dotenv

load_dotenv()

bq_client = bigquery.Client()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=redis_host, port=redis_port, db=redis_db,
                decode_responses=True)


def run_seeder():
    query = """
        SELECT
            cost_center,
            COUNT(*) AS total_transactions,
            SUM(budget_amount_brl) AS total_amount
        FROM `factory-lakehouse.factory_lakehouse.bronze_synthetic_budget`
        GROUP BY cost_center
    """

    print(f"Starting BigQuery extraction")
    query_job = bq_client.query(query)
    results = query_job.result()

    rows_processed = 0

    for row in results:
        cost_center = row.cost_center
        count = row.total_transactions
        total_sum = row.total_amount

        mean = total_sum / count if count > 0 else 0

        redis_key = f"baseline:{cost_center}"

        # Write to Redis
        r.hset(redis_key, mapping={
            "count": count,
            "total_sum": total_sum,
            "mean": mean
        })

        rows_processed += 1
        print(f"Seeded: {cost_center} (Mean: {mean:.2f})")

    print(f"Seeding Complete")
    print(f"Successfully cached {rows_processed} lines in Redis.")


if __name__ == "__main__":
    try:
        run_seeder()
    except Exception as e:
        sys.stderr.write(f"Error during seeding: {e}\n")
        sys.exit(1)
