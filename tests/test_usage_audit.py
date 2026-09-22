import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.core.database import Database


class UsageAuditDatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "audit.db"
        connection = sqlite3.connect(self.db_path)
        connection.executescript(
            """
            CREATE TABLE tokens (
                id INTEGER PRIMARY KEY,
                email TEXT,
                name TEXT
            );
            CREATE TABLE request_logs (
                id INTEGER PRIMARY KEY,
                token_id INTEGER,
                operation TEXT NOT NULL,
                request_body TEXT,
                response_body TEXT,
                status_code INTEGER NOT NULL,
                duration FLOAT NOT NULL,
                status_text TEXT,
                progress INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            );
            INSERT INTO tokens (id, email, name) VALUES
                (1, 'alice@example.com', 'Alice'),
                (2, 'bob@example.com', 'Bob');
            INSERT INTO request_logs
                (id, token_id, operation, request_body, status_code, duration, status_text, progress, created_at, updated_at)
            VALUES
                (1, 1, 'generate_image', '{"model":"imagen-4"}', 200, 2.5, 'completed', 100, datetime('now'), datetime('now')),
                (2, 1, 'generate_image', '{"model":"imagen-4"}', 500, 1.5, 'failed', 0, datetime('now'), datetime('now')),
                (3, 2, 'generate_video', '{"model":"veo"}', 200, 8.0, 'completed', 100, datetime('now'), datetime('now')),
                (4, NULL, 'generate_image', '{"model":"unknown"}', 503, 0.2, 'failed', 0, datetime('now'), datetime('now'));
            """
        )
        connection.commit()
        connection.close()
        self.database = Database(str(self.db_path))

    async def asyncTearDown(self):
        self.temp_dir.cleanup()

    async def test_aggregates_by_account_day_and_model(self):
        result = await self.database.get_usage_audit(days=7)

        self.assertEqual(result["summary"]["total_requests"], 4)
        self.assertEqual(result["summary"]["success_requests"], 2)
        self.assertEqual(result["summary"]["error_requests"], 2)
        self.assertEqual(result["summary"]["unassigned_requests"], 1)
        self.assertEqual(result["by_token"][0]["token_email"], "alice@example.com")
        self.assertEqual(result["by_token"][0]["total_requests"], 2)
        self.assertTrue(any(row["model"] == "imagen-4" for row in result["by_model"]))
        self.assertEqual(len(result["by_day"]), 1)
        self.assertEqual(len(result["recent"]), 4)

    async def test_filters_are_applied_to_summary_and_recent(self):
        result = await self.database.get_usage_audit(
            days=7,
            token_id=1,
            operation="generate_image",
            status="success",
        )

        self.assertEqual(result["summary"]["total_requests"], 1)
        self.assertEqual(result["summary"]["image_requests"], 1)
        self.assertEqual(result["filters"]["token_id"], 1)
        self.assertEqual(result["filters"]["status"], "success")
        self.assertEqual(result["recent"][0]["token_email"], "alice@example.com")


if __name__ == "__main__":
    unittest.main()
