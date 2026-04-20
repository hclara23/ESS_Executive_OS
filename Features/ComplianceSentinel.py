import json
import os
import psycopg2
from datetime import datetime
from Features.Face.Mouth import speak
from Features.TechIntel import search_code_compliance

def _pg_conn():
    uri = os.getenv("ELIO_PG_URI", "").strip()
    return psycopg2.connect(uri)

class ComplianceSentinel:
    def __init__(self):
        self.violation_history = []

    def log_violation(self, severity, category, detail):
        """Phase 2: Persistent outcome tracking"""
        try:
            conn = _pg_conn()
            cur = conn.cursor()
            cur.execute(
                """
                insert into elio_site_violations (severity, category, detail, detected_at)
                values (%s, %s, %s, %s)
                """,
                (severity, category, detail, datetime.utcnow())
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"[ComplianceSentinel] DB Log Error: {e}")
            return False

    def audit_visual_stream(self, analysis_text):
        """
        Revolutionary Phase 2: Parses vision text for specific non-compliance flags.
        """
        severity_map = {
            "CRITICAL": ["hazard", "fire", "exposed wire", "safety violation", "osha", "immediate risk"],
            "WARNING": ["improper", "not to code", "missing tag", "nec violation", "structural crack"],
            "ADVISORY": ["recommendation", "optimal", "best practice", "maintenance"]
        }
        
        detected_issues = []
        text_lower = analysis_text.lower()
        
        for severity, keywords in severity_map.items():
            for kw in keywords:
                if kw in text_lower:
                    issue = {
                        "severity": severity,
                        "category": "OSHA" if "osha" in kw else "NEC" if "nec" in kw else "Safety",
                        "detail": analysis_text
                    }
                    detected_issues.append(issue)
                    # Log to DB immediately
                    self.log_violation(severity, issue["category"], issue["detail"])
        
        if detected_issues:
            self._generate_safety_alert(detected_issues)
            return detected_issues
        return None

    def _generate_safety_alert(self, issues):
        critical_count = len([i for i in issues if i['severity'] == "CRITICAL"])
        if critical_count > 0:
            speak(f"CRITICAL COMPLIANCE ALERT: I have detected {critical_count} work-site hazards. Logging to project ledger and checking references.")
            
            for issue in issues:
                if issue['severity'] == "CRITICAL":
                    ref = search_code_compliance(issue['category'])
                    speak(f"Code Reference for {issue['category']}: {ref}")
        else:
            speak("Visual audit complete. Minor advisories detected and logged.")

compliance_sentinel = ComplianceSentinel()
