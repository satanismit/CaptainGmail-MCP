import os
# Trigger reload
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_service import run_iterative_gmail_agent, classify_emails_for_dashboard
from auth import authenticate_gmail
from gmail_service import get_dashboard_emails
from mcp_client import call_mcp_tool


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")
TOKEN_FILE = PROJECT_DIR / "token.json"


app = FastAPI(title="CAPTAINGMAIL-MCP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Prompt templates — identical to the ones previously in app.py
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES = {
    "Professional new message": (
        "Write a professional email to [recipient name or email] with subject \"[subject line]\" about "
        "[short purpose]. Keep it ~150\u2013200 words, polite, include a brief call to action, and sign as "
        "\"[Your Name]\". Don\u2019t send \u2014 prepare a draft."
    ),
    "Reply to message (by ID)": (
        "Reply to the email with message ID [MESSAGE_ID]. Say thanks, answer the question about [topic], "
        "include these points: [point 1; point 2], and end with a friendly sign-off. Create a Gmail draft only."
    ),
    "Follow-up": (
        "Draft a short follow\u2011up to [recipient or thread subject] asking for a status update. Reference earlier "
        "email dated [date] and be polite. Keep it under 80 words and offer next steps."
    ),
    "Summarize thread into reply": (
        "Summarize the recent thread about \"[topic]\" and draft a response that: 1) acknowledges received info, "
        "2) lists two action items, 3) asks one clarifying question. Make it concise and professional."
    ),
    "Summarize Email Thread": (
        "Summarize this email conversation into an overview, key points, decisions, important dates, pending questions, and action items."
    ),
    "Meeting / schedule request": (
        "Draft an email to [recipient] proposing a meeting on [two date/time options] for [purpose]. Include duration "
        "(30 mins), a proposed agenda, and ask them to confirm or propose alternatives."
    ),
    "Casual short": (
        "Write a short, casual note to [recipient] asking about [topic]. Keep it under 50 words and friendly."
    ),
    "Return JSON draft (tool)": (
        "Prepare a Gmail draft only. Return a JSON object with keys `to`, `subject`, and `body`. `to`: [email], "
        "`subject`: short descriptive subject, `body`: full email text (include signature \"[Your Name]\"). Do not send."
    ),
    "Action Items & Follow-ups": (
        "Analyze my recent email conversations and identify pending tasks, deadlines, unanswered questions, "
        "and conversations that may need follow-up. Provide evidence from the emails and offer to prepare "
        "follow-up drafts for review."
    ),
}


# ---------------------------------------------------------------------------
# Helper functions — same logic as the originals in app.py
# ---------------------------------------------------------------------------

def has_groq_configuration() -> bool:
    """Return True when the app has the Groq settings it needs."""

    return bool(
        (os.getenv("API_KEY", "").strip() or os.getenv("GROQ_API_KEY", "").strip())
        and (os.getenv("MODEL", "").strip() or os.getenv("GROQ_MODEL", "").strip())
    )


def is_gmail_connected() -> bool:
    """Return True when Gmail credentials have already been saved locally."""

    return TOKEN_FILE.exists()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


def build_http_error_detail(
    error: Exception,
    default_message: str,
) -> str:
    """Return a user-facing error message extracted from the real exception."""

    message = str(error).strip()

    if message:
        return message

    return f"{default_message}: {type(error).__name__}"


Tone = Literal["professional", "friendly", "concise", "formal"]


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict[str, str]] = []
    tone: Tone = "professional"


class DraftCreateRequest(BaseModel):
    to: str
    subject: str
    body: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/status")
def get_status() -> dict[str, bool]:
    """Check Gmail connection status and Groq configuration."""

    return {
        "gmail_connected": is_gmail_connected(),
        "ai_configured": has_groq_configuration(),
    }


@app.post("/api/auth/connect")
def connect_gmail() -> dict[str, str]:
    """Trigger Gmail OAuth flow."""

    try:
        authenticate_gmail()
        return {"status": "connected"}

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.post("/api/auth/disconnect")
def disconnect_gmail() -> dict[str, str]:
    """Remove saved Gmail token."""

    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

    return {"status": "disconnected"}


@app.get("/api/templates")
def get_templates() -> dict[str, Any]:
    """Return all prompt templates."""

    return {"templates": PROMPT_TEMPLATES}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Send a message to the AI agent and return the response."""

    cleaned_message = request.message.strip()

    if not cleaned_message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    if not is_gmail_connected():
        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected. Please connect Gmail first.",
        )

    if not has_groq_configuration():
        raise HTTPException(
            status_code=503,
            detail="API_KEY and MODEL must be configured.",
        )

    try:
        result = await run_iterative_gmail_agent(
            user_request=cleaned_message,
            conversation_history=request.conversation_history or None,
            access_token=None,
            tone=request.tone,
        )

        return {
            "answer": result.get("answer", ""),
            "tool_history": result.get("tool_history", []),
            "pending_action": result.get("pending_action"),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=build_http_error_detail(
                error,
                "An unexpected error occurred while processing your request.",
            ),
        )

    except Exception as error:
        err = traceback.format_exc()

        try:
            with open(PROJECT_DIR / "error.log", "a", encoding="utf-8") as fh:
                fh.write(
                    f"\n[{datetime.now(timezone.utc).isoformat()}] "
                    f"Chat handler exception:\n"
                )
                fh.write(err)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=build_http_error_detail(
                error,
                "An unexpected error occurred while processing your request.",
            ),
        )


@app.post("/api/draft/create")
async def create_draft(request: DraftCreateRequest) -> dict[str, Any]:
    """Create a Gmail draft after explicit user confirmation."""

    if not is_gmail_connected():
        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    cleaned_to = request.to.strip()
    cleaned_subject = request.subject.strip()
    cleaned_body = request.body.strip()

    if not cleaned_to:
        raise HTTPException(
            status_code=400,
            detail="Recipient (to) cannot be empty.",
        )

    if not cleaned_subject:
        raise HTTPException(
            status_code=400,
            detail="Subject cannot be empty.",
        )

    if not cleaned_body:
        raise HTTPException(
            status_code=400,
            detail="Body cannot be empty.",
        )

    try:
        result = await call_mcp_tool(
            tool_name="create_gmail_draft",
            arguments={
                "to": cleaned_to,
                "subject": cleaned_subject,
                "body": cleaned_body,
            },
            access_token=None,
        )

        return result

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=build_http_error_detail(
                error,
                "An unexpected error occurred while creating the Gmail draft.",
            ),
        )

    except Exception as error:
        err = traceback.format_exc()

        try:
            with open(PROJECT_DIR / "error.log", "a", encoding="utf-8") as fh:
                fh.write(
                    f"\n[{datetime.now(timezone.utc).isoformat()}] "
                    f"Draft creation exception:\n"
                )
                fh.write(err)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=build_http_error_detail(
                error,
                "An unexpected error occurred while creating the Gmail draft.",
            ),
        )


@app.get("/api/dashboard")
async def get_dashboard() -> dict[str, Any]:
    """Retrieve AI-analyzed priority inbox dashboard data."""

    if not is_gmail_connected():
        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    if not has_groq_configuration():
        raise HTTPException(
            status_code=503,
            detail="AI is not configured. Set API_KEY and MODEL in .env.",
        )

    try:
        # Step 1: Fetch email metadata from Gmail
        gmail_data = get_dashboard_emails(max_results=15)

        emails = gmail_data.get("emails", [])
        user_email = gmail_data.get("user_email", "")

        # Step 2: AI classification of emails
        ai_result = classify_emails_for_dashboard(
            emails=emails,
            user_email=user_email,
        )

        # Step 3: Enrich AI results with full email metadata
        email_lookup = {e["id"]: e for e in emails}

        important_emails = []
        for item in ai_result.get("important_emails", []):
            msg_id = item.get("id", "")
            meta = email_lookup.get(msg_id, {})
            important_emails.append({
                "message_id": msg_id,
                "thread_id": meta.get("thread_id", ""),
                "subject": meta.get("subject", "(Unknown)"),
                "sender": meta.get("sender", ""),
                "sender_name": meta.get("sender_name", ""),
                "date": meta.get("date", ""),
                "snippet": meta.get("snippet", ""),
                "priority": item.get("priority", "Medium"),
                "reason": item.get("reason", ""),
            })

        action_items = []
        for item in ai_result.get("action_items", []):
            msg_id = item.get("message_id", "")
            meta = email_lookup.get(msg_id, {})
            action_items.append({
                "task": item.get("task", ""),
                "source_subject": meta.get("subject", "(Unknown)"),
                "source_message_id": msg_id,
                "source_thread_id": meta.get("thread_id", ""),
                "deadline": item.get("deadline"),
                "priority": item.get("priority", "Medium"),
                "status": item.get("status", "Pending"),
            })

        upcoming_deadlines = []
        for item in ai_result.get("upcoming_deadlines", []):
            msg_id = item.get("message_id", "")
            meta = email_lookup.get(msg_id, {})
            upcoming_deadlines.append({
                "task": item.get("task", ""),
                "deadline": item.get("deadline", ""),
                "source_subject": meta.get("subject", "(Unknown)"),
                "source_message_id": msg_id,
                "source_thread_id": meta.get("thread_id", ""),
                "status": item.get("status", "Upcoming"),
            })

        awaiting_replies = []
        for item in ai_result.get("awaiting_replies", []):
            msg_id = item.get("message_id", "")
            meta = email_lookup.get(msg_id, {})
            awaiting_replies.append({
                "thread_id": meta.get("thread_id", ""),
                "subject": meta.get("subject", "(Unknown)"),
                "sender": meta.get("sender", ""),
                "sender_name": meta.get("sender_name", ""),
                "last_date": meta.get("date", ""),
                "reason": item.get("reason", ""),
            })

        follow_up_recommendations = []
        for item in ai_result.get("recommended_follow_ups", []):
            msg_id = item.get("message_id", "")
            meta = email_lookup.get(msg_id, {})
            follow_up_recommendations.append({
                "thread_id": meta.get("thread_id", ""),
                "subject": meta.get("subject", "(Unknown)"),
                "sender": meta.get("sender", ""),
                "sender_name": meta.get("sender_name", ""),
                "reason": item.get("reason", ""),
                "suggested_action": item.get("suggested_action", ""),
            })

        warnings: list[str] = []
        if not emails:
            warnings.append("No recent inbox emails found.")

        return {
            "summary": {
                "important_emails": len(important_emails),
                "pending_actions": len(action_items),
                "upcoming_deadlines": len(upcoming_deadlines),
                "awaiting_replies": len(awaiting_replies),
            },
            "important_emails": important_emails,
            "pending_actions": action_items,
            "upcoming_deadlines": upcoming_deadlines,
            "awaiting_replies": awaiting_replies,
            "follow_up_recommendations": follow_up_recommendations,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "warnings": warnings,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=build_http_error_detail(
                error,
                "Failed to generate dashboard data.",
            ),
        )

