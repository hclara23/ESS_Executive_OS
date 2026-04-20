import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Mock Speak and Understand to allow headless testing
import Features.Face.Mouth
import Features.Face.Ear
Features.Face.Mouth.speak = MagicMock()
Features.Face.Ear.understand = MagicMock(return_value="yes")
Features.Face.Ear.listen = MagicMock(return_value="wake up")

from Features.MemoryStore import (
    add_private_memory, 
    add_lesson, 
    save_second_brain_fact, 
    add_delegation,
    log_audit_action
)
from Features.TechIntel import search_code_compliance
from Features.BiddingHub import find_suitable_bids, prefill_submittal
from Features.AgenticWorkflows import executive_standup
from Brain.AI_Brain import ReplyBrain

class TestElioFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure we have a dummy env for PG if needed, or mock the conn
        os.environ["ELIO_PG_URI"] = "postgresql://postgres:postgres@localhost:5432/postgres"
        # Mock the DB connection entirely to avoid needing a real Postgres for this unit test
        cls.patcher = patch('psycopg2.connect')
        cls.mock_connect = cls.patcher.start()
        
    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_01_ai_brain_context(self):
        """Verify the AI Brain includes personality and lessons."""
        with patch('openai.resources.chat.completions.Completions.create') as mock_openai:
            mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Test Response", tool_calls=None))]
            resp = ReplyBrain("Hello Elio")
            self.assertIsNotNone(resp)
            # Check if the mock was called (implies the logic reached the API call)
            self.assertTrue(mock_openai.called)

    def test_02_memory_schema_mock(self):
        """Test that memory functions attempt to call DB (via mock)."""
        add_private_memory("alex", "Test private note")
        # Verify the mock cursor executed an insert
        self.assertTrue(self.mock_connect.return_value.cursor.return_value.execute.called)

    def test_03_tech_intel_oracle(self):
        """Test the Code Oracle logic (Local vs AI)."""
        # Test Local Hit
        res = search_code_compliance("burial depth")
        self.assertIn("NEC 300.5", res)
        
        # Test AI Fallback
        with patch('Features.TechIntel.ReplyBrain', return_value="AI Engineering Answer"):
            res_ai = search_code_compliance("unknown technical query")
            self.assertEqual(res_ai, "AI Engineering Answer")

    def test_04_bidding_hub_logic(self):
        """Test bid finding and drafting."""
        Features.Face.Ear.understand.return_value = "draft"
        # Mocking the second voice input for ID
        with patch('Features.Face.Ear.understand', side_effect=["yes", "BID-001"]):
            bids = find_suitable_bids("alex")
            self.assertGreater(len(bids), 0)

    def test_05_delegation_flow(self):
        """Test task delegation logic."""
        add_delegation("sandra", "alex", "Review schematics")
        self.assertTrue(self.mock_connect.return_value.cursor.return_value.execute.called)

    def test_06_audit_logging(self):
        """Ensure sensitive actions trigger audit logs."""
        log_audit_action("admin", "TEST_ACTION", "Details")
        self.assertTrue(self.mock_connect.return_value.cursor.return_value.execute.called)

if __name__ == "__main__":
    unittest.main()
