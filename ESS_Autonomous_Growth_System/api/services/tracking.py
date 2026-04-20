import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import text

class TrackingEngine:
    """Change tracking, diff, and rollback engine."""
    
    async def create_snapshot(
        self,
        db,
        content_id: str,
        snapshot_data: Dict[str, Any],
        snapshot_type: str = "before",
        reason: str = "",
        automation_id: Optional[str] = None,
    ) -> str:
        import uuid
        snapshot_id = str(uuid.uuid4())
        await db.execute(
            text(
                """INSERT INTO snapshots (id, content_id, snapshot_data, snapshot_type, reason, automation_id)
                   VALUES (:id, :content_id, :snapshot_data, :snapshot_type, :reason, :automation_id)"""
            ),
            {
                "id": snapshot_id,
                "content_id": content_id,
                "snapshot_data": json.dumps(snapshot_data),
                "snapshot_type": snapshot_type,
                "reason": reason,
                "automation_id": automation_id,
            }
        )
        await db.commit()
        return snapshot_id
    
    async def create_diff(
        self,
        db,
        before_snapshot_id: str,
        after_snapshot_id: str,
        diff_data: Dict[str, Any],
        summary: str = "",
    ) -> str:
        import uuid
        from diff_match_patch import diff_match_patch
        dmp = diff_match_patch()
        
        diff_id = str(uuid.uuid4())
        await db.execute(
            text(
                """INSERT INTO diffs (id, before_snapshot_id, after_snapshot_id, diff_data, summary)
                   VALUES (:id, :before_id, :after_id, :diff_data, :summary)"""
            ),
            {
                "id": diff_id,
                "before_id": before_snapshot_id,
                "after_id": after_snapshot_id,
                "diff_data": json.dumps(diff_data),
                "summary": summary,
            }
        )
        await db.commit()
        return diff_id
    
    async def compute_diff(self, before_content: str, after_content: str) -> Dict[str, Any]:
        from diff_match_patch import diff_match_patch
        dmp = diff_match_patch()
        diffs = dmp.diff_main(before_content, after_content)
        dmp.diff_cleanupSemantic(diffs)
        
        additions = []
        deletions = []
        for op, text in diffs:
            if op == 1:
                additions.append(text)
            elif op == -1:
                deletions.append(text)
        
        return {
            "additions": additions,
            "deletions": deletions,
            "changes_count": len([d for d in diffs if d[0] != 0]),
            "added_chars": sum(len(a) for a in additions),
            "removed_chars": sum(len(d) for d in deletions),
        }
    
    async def rollback_to_snapshot(
        self,
        db,
        content_id: str,
        snapshot_id: str,
    ) -> Dict[str, Any]:
        result = await db.execute(
            text("SELECT snapshot_data FROM snapshots WHERE id = :id"),
            {"id": snapshot_id}
        )
        row = result.fetchone()
        if not row:
            return {"success": False, "error": "Snapshot not found"}
        
        snapshot_data = json.loads(row[0])
        
        await db.execute(
            text(
                """UPDATE content_versions 
                   SET content = :content, meta_description = :meta, title = :title,
                       updated_at = NOW()
                   WHERE id = :content_id"""
            ),
            {
                "content": snapshot_data.get("content"),
                "meta": snapshot_data.get("meta_description"),
                "title": snapshot_data.get("title"),
                "content_id": content_id,
            }
        )
        await db.commit()
        
        return {
            "success": True,
            "content_id": content_id,
            "rolled_back_to": snapshot_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def get_change_history(self, db, content_id: str) -> List[Dict[str, Any]]:
        result = await db.execute(
            text(
                """SELECT s.id, s.snapshot_type, s.reason, s.created_at, s.automation_id,
                          d.id as diff_id, d.summary as diff_summary
                   FROM snapshots s
                   LEFT JOIN diffs d ON d.before_snapshot_id = s.id OR d.after_snapshot_id = s.id
                   WHERE s.content_id = :content_id
                   ORDER BY s.created_at DESC"""
            ),
            {"content_id": content_id}
        )
        rows = result.fetchall()
        return [
            {
                "snapshot_id": r[0],
                "type": r[1],
                "reason": r[2],
                "created_at": r[3].isoformat() if r[3] else None,
                "automation_id": r[4],
                "diff_id": r[5],
                "diff_summary": r[6],
            }
            for r in rows
        ]

tracking_engine = TrackingEngine()
