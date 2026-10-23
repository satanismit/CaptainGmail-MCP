import sys

with open("api.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add imports
old_import = "from ai_service import run_iterative_gmail_agent\nfrom auth import authenticate_gmail\nfrom mcp_client import call_mcp_tool"
new_import = "from ai_service import run_iterative_gmail_agent, classify_emails_for_dashboard\nfrom auth import authenticate_gmail\nfrom gmail_service import get_dashboard_emails\nfrom mcp_client import call_mcp_tool"

if old_import not in code:
    print("ERROR: Import target not found")
    sys.exit(1)

code = code.replace(old_import, new_import, 1)

# 2. Add dashboard endpoint at end
dashboard_endpoint = '''


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
'''

code = code.rstrip() + dashboard_endpoint + "\n"

with open("api.py", "w", encoding="utf-8") as f:
    f.write(code)
print("api.py updated successfully")
