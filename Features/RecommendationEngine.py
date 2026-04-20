import os
import json
import psycopg2
from datetime import datetime

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def generate_proactive_recommendations():
    """
    Analyzes project health and financials to generate dashboard recommendations.
    """
    conn = _pg_conn()
    cur = conn.cursor()
    
    # 1. Analyze Project Health (Bid vs Actual)
    cur.execute("""
        select title, estimated_cost, coalesce(sum(e.total_amount), 0) as actual
        from elio_bid_opportunities b
        left join elio_expenses e on b.project_tag = e.project_tag
        where b.status = 'approved'
        group by b.title, b.estimated_cost
    """)
    projects = cur.fetchall()
    
    recommendations = []
    
    for p in projects:
        title, bid, actual = p[0], float(p[1] or 0), float(p[2])
        if actual > (bid * 0.8) and actual < bid:
            recommendations.append({
                "user": "sandra",
                "title": f"Budget Alert: {title}",
                "desc": f"Project has reached 80% of its ${bid:,.2f} budget. Review recent expenses.",
                "category": "financial",
                "prompt": f"Elio, show me a detailed expense breakdown for {title}."
            })
            
    # 2. Analyze Vendor Compliance
    cur.execute("select name from elio_vendors where status = 'pending' or status = 'expired'")
    non_compliant = cur.fetchall()
    if non_compliant:
        recommendations.append({
            "user": "sandra",
            "title": "Compliance Action Needed",
            "desc": f"{len(non_compliant)} vendors have missing or expired documents.",
            "category": "operational",
            "prompt": "Elio, send compliance reminder emails to all non-compliant vendors."
        })

    # Save to DB
    for r in recommendations:
        cur.execute(
            """
            insert into elio_ai_recommendations (user_name, title, description, category, action_prompt, created_at)
            values (%s, %s, %s, %s, %s, %s)
            on conflict do nothing;
            """,
            (r['user'], r['title'], r['desc'], r['category'], r['prompt'], datetime.utcnow())
        )
        
    conn.commit()
    cur.close()
    conn.close()
    return f"Generated {len(recommendations)} proactive insights."
