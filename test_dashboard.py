import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import api
import ai_service
import gmail_service


class TestDashboardAndCoreFeatures(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api.app)

    # 1. Dashboard response structure and summary counts
    @patch("api.get_dashboard_emails")
    @patch("api.classify_emails_for_dashboard")
    @patch("api.is_gmail_connected", return_value=True)
    @patch("api.has_groq_configuration", return_value=True)
    def test_dashboard_response_structure_and_counts(
        self, mock_groq_cfg, mock_gmail_conn, mock_classify, mock_get_emails
    ):
        mock_get_emails.return_value = {
            "user_email": "test@example.com",
            "emails": [
                {
                    "id": "msg_1",
                    "thread_id": "th_1",
                    "sender": "sender1@example.com",
                    "sender_name": "Sender One",
                    "recipient": "test@example.com",
                    "subject": "Urgent Project Deadline",
                    "date": "Fri, 24 Oct 2026 10:00:00 +0000",
                    "snippet": "Please submit the final report by Friday.",
                },
                {
                    "id": "msg_2",
                    "thread_id": "th_2",
                    "sender": "sender2@example.com",
                    "sender_name": "Sender Two",
                    "recipient": "test@example.com",
                    "subject": "Coffee catch up?",
                    "date": "Thu, 23 Oct 2026 15:30:00 +0000",
                    "snippet": "Are you free for coffee tomorrow?",
                },
            ],
        }

        mock_classify.return_value = {
            "important_emails": [
                {"id": "msg_1", "reason": "Mentions urgent project deadline", "priority": "High"}
            ],
            "action_items": [
                {
                    "task": "Submit final report",
                    "message_id": "msg_1",
                    "deadline": "Friday",
                    "priority": "High",
                    "status": "Pending",
                }
            ],
            "upcoming_deadlines": [
                {
                    "task": "Submit final report",
                    "deadline": "Friday",
                    "message_id": "msg_1",
                    "status": "Upcoming",
                }
            ],
            "awaiting_replies": [
                {"message_id": "msg_2", "reason": "Question about coffee catch up"}
            ],
            "recommended_follow_ups": [
                {
                    "message_id": "msg_1",
                    "reason": "Ensure report is on track",
                    "suggested_action": "Confirm receipt and progress",
                }
            ],
        }

        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validate top-level keys
        self.assertIn("summary", data)
        self.assertIn("important_emails", data)
        self.assertIn("pending_actions", data)
        self.assertIn("upcoming_deadlines", data)
        self.assertIn("awaiting_replies", data)
        self.assertIn("follow_up_recommendations", data)
        self.assertIn("retrieved_at", data)
        self.assertIn("warnings", data)

        # Validate summary counts match data lengths
        summary = data["summary"]
        self.assertEqual(summary["important_emails"], 1)
        self.assertEqual(summary["pending_actions"], 1)
        self.assertEqual(summary["upcoming_deadlines"], 1)
        self.assertEqual(summary["awaiting_replies"], 1)

        # Validate enriched metadata
        self.assertEqual(data["important_emails"][0]["subject"], "Urgent Project Deadline")
        self.assertEqual(data["important_emails"][0]["sender_name"], "Sender One")
        self.assertEqual(data["important_emails"][0]["priority"], "High")

    # 2. Email classification using mocked Groq response
    @patch("ai_service.chat_completion_with_retry")
    def test_classify_emails_for_dashboard(self, mock_chat):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "important_emails": [{"id": "m1", "reason": "Security Alert", "priority": "High"}],
                            "action_items": [{"task": "Review login", "message_id": "m1", "deadline": "None explicitly stated", "priority": "High", "status": "Pending"}],
                            "upcoming_deadlines": [],
                            "awaiting_replies": [],
                            "recommended_follow_ups": [],
                        }
                    )
                )
            )
        ]
        mock_chat.return_value = mock_response

        emails = [
            {
                "id": "m1",
                "sender": "security@google.com",
                "sender_name": "Google Security",
                "subject": "New login alert",
                "date": "Oct 23",
                "snippet": "New sign-in detected on your account.",
            }
        ]
        result = ai_service.classify_emails_for_dashboard(emails, user_email="user@gmail.com")
        self.assertEqual(len(result["important_emails"]), 1)
        self.assertEqual(result["important_emails"][0]["reason"], "Security Alert")
        self.assertEqual(len(result["action_items"]), 1)

    # 3. Empty inbox scenario
    @patch("api.get_dashboard_emails")
    @patch("api.classify_emails_for_dashboard")
    @patch("api.is_gmail_connected", return_value=True)
    @patch("api.has_groq_configuration", return_value=True)
    def test_empty_inbox_scenario(
        self, mock_groq_cfg, mock_gmail_conn, mock_classify, mock_get_emails
    ):
        mock_get_emails.return_value = {"user_email": "user@example.com", "emails": []}
        mock_classify.return_value = {
            "important_emails": [],
            "action_items": [],
            "upcoming_deadlines": [],
            "awaiting_replies": [],
            "recommended_follow_ups": [],
        }

        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["important_emails"], 0)
        self.assertEqual(data["summary"]["pending_actions"], 0)
        self.assertTrue(len(data["warnings"]) > 0)

    # 4. Malformed or incomplete AI responses
    @patch("ai_service.chat_completion_with_retry")
    def test_malformed_ai_response_handling(self, mock_chat):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="INVALID_JSON_RESPONSE"))
        ]
        mock_chat.return_value = mock_response

        emails = [{"id": "m1", "subject": "Test", "sender": "a@b.com", "date": "Oct 23", "snippet": "abc"}]
        result = ai_service.classify_emails_for_dashboard(emails, user_email="user@gmail.com")
        self.assertIn("important_emails", result)
        self.assertEqual(len(result["important_emails"]), 0)

    # 5. Gmail connection required for dashboard
    @patch("api.is_gmail_connected", return_value=False)
    def test_dashboard_requires_gmail_connection(self, mock_conn):
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Gmail is not connected", response.json()["detail"])

    # 6. Follow-up draft confirmation required (Write tools intercepted)
    def test_draft_creation_requires_confirmation(self):
        # Confirm create_gmail_draft is classified as a WRITE_TOOL in ai_service
        self.assertIn("create_gmail_draft", ai_service.WRITE_TOOLS)

    # 7. Tone control validation
    def test_tones_validation(self):
        for tone in ["professional", "friendly", "concise", "formal"]:
            self.assertIn(tone, ai_service.VALID_TONES)

    # 8. Templates consistency
    def test_templates_presence(self):
        response = self.client.get("/api/templates")
        self.assertEqual(response.status_code, 200)
        templates = response.json()["templates"]
        self.assertIn("Action Items & Follow-ups", templates)
        self.assertIn("Summarize Email Thread", templates)


if __name__ == "__main__":
    unittest.main()
