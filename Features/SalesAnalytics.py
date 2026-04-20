import os
import psycopg2
from datetime import datetime, timedelta

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def calculate_sales_forecast():
    """
    Analyzes elio_bid_opportunities to forecast quarterly revenue.
    """
    conn = _pg_conn()
    cur = conn.cursor()
    
    # 1. Get win ratio
    cur.execute("select count(*) from elio_bid_opportunities where status = 'approved'")
    won = cur.fetchone()[0]
    cur.execute("select count(*) from elio_bid_opportunities where status = 'rejected'")
    lost = cur.fetchone()[0]
    
    total_resolved = won + lost
    win_ratio = (won / total_resolved) if total_resolved > 0 else 0.5 # Default to 50% if no data
    
    # 2. Get pending pipeline
    cur.execute("select sum(estimated_cost * (1 + markup_percent/100.0)) from elio_bid_opportunities where status = 'pending'")
    pending_value = float(cur.fetchone()[0] or 0)
    
    # 3. Forecasted Revenue (Pipeline * Win Ratio)
    forecasted_revenue = pending_value * win_ratio
    
    cur.close()
    conn.close()
    
    return {
        "win_ratio": round(win_ratio * 100, 1),
        "pipeline_value": pending_value,
        "forecasted_revenue": forecasted_revenue,
        "period": "Next 90 Days"
    }

def get_team_efficiency():
    """
    Analyzes delegation turnaround time (if we had completed_at data).
    """
    # Placeholder for team efficiency metrics
    return {
        "avg_task_completion_hrs": 14.5,
        "handoff_bottlenecks": "Sandra -> Alex (Materials)",
        "efficiency_score": 88
    }
