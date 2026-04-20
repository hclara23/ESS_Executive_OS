import os
import json
from datetime import datetime
import psycopg2
from Features.Storage import upload_to_elio_storage
from server.ai_provider import chat_completion
from server.subagent_client import call_subagent

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

def get_pending_opportunities(limit=3):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        "select id, title, description, technical_data, draft_proposal, source_url from elio_bid_opportunities where status = 'pending' order by created_at desc limit %s",
        (limit,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "description": r[2], "technical_data": r[3], "draft_proposal": r[4], "source_url": r[5]}
        for r in rows
    ]

def save_opportunity(title, description, source_url, tech_data=None, draft=None):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        insert into elio_bid_opportunities (title, description, technical_data, draft_proposal, source_url, created_at)
        values (%s, %s, %s, %s, %s, %s) returning id;
        """,
        (title, description, json.dumps(tech_data) if tech_data else "{}", draft, source_url, datetime.utcnow())
    )
    opp_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return opp_id

def find_new_opportunities():
    """
    Autonomous agent logic to find new bids ESS could submit for.
    Mocking the search results for now.
    """
    pending = get_pending_opportunities(limit=10)
    if len(pending) >= 3:
        return "Batch is full. Resolve current 3 proposals first."

    # In a real scenario, we'd use a Search Tool or scrape specific portals.
    # Here we ask Elio's brain to 'simulate' finding a highly relevant bid.
    prompt = """
    You are Elio's Bidding Scout. 
    Simulate finding a realistic new bidding opportunity for ESS (Engineering & Site Services).
    ESS specializes in: Electrical compliance, VFD configurations, site audits, and technical engineering management.
    
    Return a JSON object:
    {
      "title": "Project Name",
      "description": "Short summary of work needed",
      "source_url": "https://example.com/bids/123",
      "requirement_summary": "Summary of technical needs"
    }
    """
    
    try:
        response = chat_completion(
            "bidding_scout",
            messages=[{"role": "system", "content": "You are a bidding scout. Output JSON only."},
                      {"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.2,
        )
        data = json.loads(response.choices[0].message.content)
        
        # Prepare the draft immediately
        opp_id = save_opportunity(data['title'], data['description'], data['source_url'])
        prepare_proposal(opp_id)
        
        return f"Found and prepared new opportunity: {data['title']}"
    except Exception as e:
        return f"Error scouting for bids: {e}"

def prepare_proposal(opp_id):
    """
    Takes an opportunity, analyzes technical docs (if any), and pre-fills a proposal.
    """
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("select title, description from elio_bid_opportunities where id = %s", (opp_id,))
    row = cur.fetchone()
    if not row: return
    
    title, desc = row[0], row[1]
    prompt = f"""
    Draft a professional bid proposal for the following project:
    Title: {title}
    Description: {desc}
    
    Include sections for: 
    1. Executive Summary
    2. Technical Approach (mentioning ESS standards)
    3. Estimated Timeline
    4. Compliance (NEC/OSHA)
    
    Use Markdown format.
    """
    
    try:
        subagent_result = call_subagent(
            "/tasks/proposal-draft",
            {"title": title, "description": desc},
            timeout=30,
        )
        if subagent_result:
            draft = subagent_result.get("draft", "")
        else:
            response = chat_completion(
                "proposal_draft",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            draft = response.choices[0].message.content

        cur.execute("update elio_bid_opportunities set draft_proposal = %s where id = %s", (draft, opp_id))
        conn.commit()
    except Exception as e:
        print(f"Error preparing proposal: {e}")
    finally:
        cur.close()
        conn.close()

def extract_technical_data(opp_id, file_path):
    # ... logic
    return {}

def find_similar_projects(bid_id):
    """
    Uses keyword matching to find previous projects with similar titles/descriptions.
    """
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("select title from elio_bid_opportunities where id = %s", (bid_id,))
    row = cur.fetchone()
    if not row: return []
    
    title = row[0]
    # Simple similarity based on words in title
    words = [w for w in title.split() if len(w) > 3]
    if not words: return []
    
    query = "select id, title, estimated_cost, status from elio_bid_opportunities where id != %s and ("
    query += " or ".join(["title ilike %s" for _ in words])
    query += ") order by created_at desc limit 3"
    
    cur.execute(query, [bid_id] + [f"%{w}%" for w in words])
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "cost": float(r[2] or 0), "status": r[3]} for r in rows]

def get_bid_quotes(bid_id):
    conn = _pg_conn()
    cur = conn.cursor()
    cur.execute("""
        select q.item_description, q.quoted_price, v.name, q.status 
        from elio_bid_quotes q
        join elio_vendors v on q.vendor_id = v.id
        where q.opportunity_id = %s
    """, (bid_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"item": r[0], "price": float(r[1] or 0), "vendor": r[2], "status": r[3]} for r in rows]
