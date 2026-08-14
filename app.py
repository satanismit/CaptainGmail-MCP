import asyncio
import os
from pathlib import Path
from typing import Any
import traceback
from datetime import datetime

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from ai_service import run_iterative_gmail_agent
from auth import authenticate_gmail
from mcp_client import call_mcp_tool


st.set_page_config(
    page_title="CAPTAINGMAIL MCP",
    page_icon="📧",
    layout="centered",
)


PROJECT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = PROJECT_DIR / "token.json"


def load_hosted_secrets() -> None:
    """Expose hosted Streamlit secrets as process environment values."""

    secret_names = (
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "GOOGLE_CLIENT_SECRETS_JSON",
        "GOOGLE_OAUTH_CLIENT_SECRETS_JSON",
        "GMAIL_CLIENT_SECRETS_JSON",
    )

    try:
        secrets = st.secrets
    except StreamlitSecretNotFoundError:
        return

    for secret_name in secret_names:
        try:
            secret_value = secrets[secret_name]
        except StreamlitSecretNotFoundError:
            return
        except KeyError:
            continue

        os.environ[secret_name] = str(secret_value)


def has_groq_configuration() -> bool:
    """Return True when the app has the Groq settings it needs."""

    return bool(
        os.getenv("GROQ_API_KEY", "").strip()
        and os.getenv("GROQ_MODEL", "").strip()
    )


def is_gmail_connected() -> bool:
    """Return True when Gmail credentials have already been saved locally."""

    return TOKEN_FILE.exists()


def connect_gmail() -> None:
    """Run Gmail OAuth and save the resulting token locally."""

    try:
        with st.spinner("Connecting Gmail..."):
            authenticate_gmail()
    except Exception as error:
        st.error(str(error))
        return

    st.session_state.gmail_connected = True
    st.success("Gmail connected successfully.")
    st.rerun()


def disconnect_gmail() -> None:
    """Forget the local Gmail token and reset the app state."""

    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

    st.session_state.gmail_connected = False
    st.session_state.messages = []
    st.session_state.last_tool_history = []
    st.session_state.pending_action = None
    st.rerun()


load_hosted_secrets()


def render_prompt_templates_sidebar() -> None:
    """Render prompt templates in the sidebar and expose a selected template for copying."""

    templates = {
        "Professional new message": (
            "Write a professional email to [recipient name or email] with subject \"[subject line]\" about "
            "[short purpose]. Keep it ~150–200 words, polite, include a brief call to action, and sign as "
            "\"[Your Name]\". Don’t send — prepare a draft."
        ),
        "Reply to message (by ID)": (
            "Reply to the email with message ID [MESSAGE_ID]. Say thanks, answer the question about [topic], "
            "include these points: [point 1; point 2], and end with a friendly sign-off. Create a Gmail draft only."
        ),
        "Follow-up": (
            "Draft a short follow‑up to [recipient or thread subject] asking for a status update. Reference earlier "
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

    st.sidebar.header("Prompt Templates")

    # Ensure session state default exists before creating the widget
    if "selected_template_box" not in st.session_state:
        st.session_state.selected_template_box = st.session_state.get(
            "selected_template", ""
        )

    # Selected template box for easy copy/edit
    selected = st.sidebar.text_area(
        "Selected template (edit and copy into chat)",
        value=st.session_state.selected_template_box,
        height=160,
        key="selected_template_box",
    )

    # Allow templates to populate the selected box
    for name, text in templates.items():
        with st.sidebar.expander(name, expanded=False):
            st.write(text)
            st.button(
                f"Select: {name}",
                key=f"select_{name}",
                on_click=_set_selected_template,
                args=(text,),
            )


def _set_selected_template(text: str) -> None:
    """Callback to set the selected template in session state."""

    st.session_state.selected_template = text
    # assign to the widget-backed key via session_state in callback (allowed)
    st.session_state.selected_template_box = text



render_prompt_templates_sidebar()


def require_gmail_connection() -> None:
    """Stop the app until Gmail OAuth has completed locally."""

    if st.session_state.get("gmail_connected") or is_gmail_connected():
        st.session_state.gmail_connected = True
        return

    st.title("CAPTAINGMAIL-MCP")
    st.caption("Connect Gmail before chatting with your inbox.")

    st.write(
        "Connect your Gmail account to search and summarize "
        "your emails."
    )

    if st.button(
        "Connect Gmail",
        type="primary",
        use_container_width=False,
    ):
        connect_gmail()

    st.stop()


def initialize_session_state() -> None:
    """Initialize values that must survive Streamlit reruns."""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_tool_history" not in st.session_state:
        st.session_state.last_tool_history = []

    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None


def display_tool_history(
    tool_history: list[dict[str, Any]],
) -> None:
    """Display MCP tool activity in a compact expander."""

    if not tool_history:
        return

    with st.expander(
        f"Tool activity ({len(tool_history)} call(s))"
    ):
        for index, tool_call in enumerate(
            tool_history,
            start=1,
        ):
            st.markdown(
                f"**{index}. `{tool_call['tool_name']}`**"
            )

            st.json(
                tool_call["arguments"]
            )


def display_pending_draft(
    pending_action: dict[str, Any],
) -> None:
    """Display a pending Gmail draft for user approval."""

    if (
        not pending_action
        or pending_action.get("tool_name")
        != "create_gmail_draft"
    ):
        return

    arguments = pending_action.get(
        "arguments",
        {},
    )

    to = arguments.get("to", "")
    subject = arguments.get("subject", "")
    body = arguments.get("body", "")

    st.divider()
    st.subheader("Draft preview")

    st.write(f"**To:** {to}")
    st.write(f"**Subject:** {subject}")

    st.text_area(
        "Body",
        value=body,
        height=220,
        disabled=True,
        key="pending_draft_body_preview",
    )

    confirm_column, cancel_column = st.columns(2)

    with confirm_column:
        create_clicked = st.button(
            "Create Draft",
            type="primary",
            use_container_width=True,
        )

    with cancel_column:
        cancel_clicked = st.button(
            "Cancel",
            use_container_width=True,
        )

    if create_clicked:
        try:
            with st.spinner(
                "Creating Gmail draft..."
            ):
                result = asyncio.run(
                    call_mcp_tool(
                        tool_name="create_gmail_draft",
                        arguments={
                            "to": to,
                            "subject": subject,
                            "body": body,
                        },
                        access_token=None,
                    )
                )

            st.session_state.pending_action = None

            st.success(
                "Draft created successfully in Gmail."
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "Draft created successfully in Gmail. "
                        "It has not been sent."
                    ),
                }
            )

            st.rerun()

        except RuntimeError as error:
            st.error(str(error))

        except Exception:
            err = traceback.format_exc()
            st.error("An unexpected error occurred while creating the Gmail draft.")
            st.text("Error details:")
            st.code(err)

            try:
                with open(PROJECT_DIR / "error.log", "a", encoding="utf-8") as fh:
                    fh.write(f"\n[{datetime.utcnow().isoformat()}] Draft creation exception:\n")
                    fh.write(err)
            except Exception:
                pass

    if cancel_clicked:
        st.session_state.pending_action = None

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Draft creation cancelled. "
                    "No Gmail draft was created."
                ),
            }
        )

        st.rerun()
require_gmail_connection()

initialize_session_state()

st.title("CAPTAINGMAIL-MCP")
st.caption(
    "AI-powered Gmail assistant using Groq and MCP"
)

if not has_groq_configuration():
    st.warning(
        "Set GROQ_API_KEY and GROQ_MODEL in environment variables or "
        "a .streamlit/secrets.toml file to enable chat."
    )

# Minimal horizontal control bar instead of a sidebar
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.session_state.get("gmail_connected") or is_gmail_connected():
        st.session_state.gmail_connected = True
        st.caption("Connected: **Gmail**")

with col2:
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_tool_history = []
        st.session_state.pending_action = None
        st.rerun()

with col3:
    if st.button("Disconnect", use_container_width=True):
        disconnect_gmail()

st.divider()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("tool_history"):
            display_tool_history(
                message["tool_history"]
            )


prompt = st.chat_input(
    "Ask something about your Gmail inbox",
    disabled=not has_groq_configuration(),
)

if prompt:
    if not has_groq_configuration():
        st.error(
            "Configure GROQ_API_KEY and GROQ_MODEL before using chat."
        )
        st.stop()

    conversation_history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in st.session_state.messages
        if message.get("role") in {"user", "assistant"}
        and message.get("content")
    ]

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            with st.spinner(
                "CAPTAINGMAIL-MCP is checking your Gmail..."
            ):
                result = asyncio.run(
                    run_iterative_gmail_agent(
                        user_request=prompt,
                        conversation_history=conversation_history,
                        access_token=None,
                    )
                )

            answer = result["answer"]
            tool_history = result["tool_history"]
            pending_action = result.get("pending_action")

            st.session_state.pending_action = pending_action

            if pending_action:
                st.info(
                    "I prepared a Gmail draft. Review it below before creating it."
                )
            elif answer:
                st.markdown(answer)

            display_tool_history(tool_history)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "I prepared a Gmail draft. Review it below before creating it."
                    if pending_action
                    else answer
                ),
                "tool_history": tool_history,
            }
        )

        st.session_state.last_tool_history = (
            tool_history
        )
        st.rerun()

    except ValueError as error:
        with st.chat_message("assistant"):
            st.warning(str(error))

    except RuntimeError as error:
        with st.chat_message("assistant"):
            st.error(str(error))

    except Exception:
        err = traceback.format_exc()
        # Show the traceback in the UI for debugging
        with st.chat_message("assistant"):
            st.error("An unexpected error occurred while processing your request.")
            st.text("Error details:")
            st.code(err)

        # Also write to a local log file with timestamp
        try:
            with open(PROJECT_DIR / "error.log", "a", encoding="utf-8") as fh:
                fh.write(f"\n[{datetime.utcnow().isoformat()}] Chat handler exception:\n")
                fh.write(err)
        except Exception:
            pass


if st.session_state.pending_action:
    display_pending_draft(
        st.session_state.pending_action
    )