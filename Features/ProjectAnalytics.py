import os
import psycopg2
from datetime import datetime, timedelta

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def calculate_project_forecast(project_tag):
    """
    ML-lite trend forecasting for project costs.
    Uses linear regression logic to predict final spend based on velocity.
    """
    conn = _pg_conn()
    cur = conn.cursor()
    
    # 1. Get original bid
    cur.execute("select total_amount, created_at from elio_bid_opportunities where project_tag = %s", (project_tag,))
    bid_row = cur.fetchone()
    if not bid_row: return "Project not found."
    bid_total = float(bid_row[0] or 0)
    start_date = bid_row[1]
    
    # 2. Get current spend over time
    cur.execute("select total_amount, created_at from elio_expenses where project_tag = %s order by created_at", (project_tag,))
    expenses = cur.fetchall()
    cur.close()
    conn.close()
    
    if not expenses: return "No expenses recorded yet for forecasting."
    
    current_total = sum(float(e[0]) for e in expenses)
    days_passed = (datetime.now() - start_date).days or 1
    daily_velocity = current_total / days_passed
    
    # Predict based on 90-day cycle
    projected_total = daily_velocity * 90 
    
    status = "On Track" if projected_total <= bid_total else "Risk: Over Budget"
    
    return {
        "projected_total": projected_total,
        "daily_velocity": daily_velocity,
        "status": status,
        "variance": projected_total - bid_total
    }
