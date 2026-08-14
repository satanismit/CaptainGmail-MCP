import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_service import run_iterative_gmail_agent
from auth import authenticate_gmail
from mcp_client import call_mcp_tool


load_dotenv()


PROJECT_DIR = Path(__file__).resolve().parent
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
}


# ---------------------------------------------------------------------------
# Helper functions — same logic as the originals in app.py
# ---------------------------------------------------------------------------

def has_groq_configuration() -> bool:
    """Return True when the app has the Groq settings it needs."""

    return bool(
        os.getenv("GROQ_API_KEY", "").strip()
        and os.getenv("GROQ_MODEL", "").strip()
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


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict[str, str]] = []


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
        "groq_configured": has_groq_configuration(),
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
            detail="GROQ_API_KEY and GROQ_MODEL must be configured.",
        )

    try:
        result = await run_iterative_gmail_agent(
            user_request=cleaned_message,
            conversation_history=request.conversation_history or None,
            access_token=None,
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
