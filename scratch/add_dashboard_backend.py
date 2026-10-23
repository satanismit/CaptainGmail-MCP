import sys

# 1. Add get_dashboard_emails to gmail_service.py
with open("gmail_service.py", "r", encoding="utf-8") as f:
    gmail_code = f.read()

if "def get_dashboard_emails" not in gmail_code:
    get_dashboard_emails_def = """

def get_dashboard_emails(
    max_results: int = 15,
    access_token: str | None = None,
) -> dict[str, Any]:
    \"\"\"Retrieve recent inbox emails and user profile for dashboard analysis.\"\"\"
    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    service = build_gmail_service(access_token=access_token)
    user_email = ""
    try:
        profile = service.users().getProfile(userId="me").execute()
        user_email = profile.get("emailAddress", "").lower()
    except Exception:
        pass

    try:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=min(max_results, 30),
            )
            .execute()
        )
        messages = response.get("messages", [])
        email_items: list[dict[str, Any]] = []

        for item in messages:
            msg_id = item["id"]
            msg_data = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date", "To"],
                )
                .execute()
            )
            headers = msg_data.get("payload", {}).get("headers", [])
            sender = get_header(headers, "From")
            subject = get_header(headers, "Subject") or "(No subject)"
            date_str = get_header(headers, "Date")
            recipient = get_header(headers, "To")
            snippet = msg_data.get("snippet", "")
            thread_id = msg_data.get("threadId", msg_id)

            email_items.append(
                {
                    "id": msg_id,
                    "thread_id": thread_id,
                    "sender": sender,
                    "sender_name": extract_sender_name(sender),
                    "recipient": recipient,
                    "subject": subject,
                    "date": date_str,
                    "snippet": snippet,
                }
            )

        return {
            "user_email": user_email,
            "emails": email_items,
        }
    except HttpError as error:
        raise RuntimeError(
            f"Failed to retrieve dashboard emails: {error}"
        ) from error
"""
    gmail_code = gmail_code.rstrip() + "\n" + get_dashboard_emails_def + "\n"
    with open("gmail_service.py", "w", encoding="utf-8") as f:
        f.write(gmail_code)
    print("Added get_dashboard_emails to gmail_service.py")
else:
    print("get_dashboard_emails already present in gmail_service.py")

# 2. Add classify_emails_for_dashboard to ai_service.py
with open("ai_service.py", "r", encoding="utf-8") as f:
    ai_code = f.read()

if "def classify_emails_for_dashboard" not in ai_code:
    classify_def = """

def classify_emails_for_dashboard(
    emails: list[dict[str, Any]],
    user_email: str = "",
) -> dict[str, Any]:
    \"\"\"Analyze recent emails using Groq and classify into dashboard categories.\"\"\"
    empty_result: dict[str, list[Any]] = {
        "important_emails": [],
        "action_items": [],
        "upcoming_deadlines": [],
        "awaiting_replies": [],
        "recommended_follow_ups": [],
    }

    if not emails:
        return empty_result

    client = get_groq_client()
    model_name = get_model_name()

    prompt_data = [
        {
            "id": e["id"],
            "sender": e.get("sender_name", e.get("sender", "")),
            "sender_raw": e.get("sender", ""),
            "subject": e.get("subject", ""),
            "date": e.get("date", ""),
            "snippet": e.get("snippet", "")[:200],
        }
        for e in emails
    ]

    system_instruction = (
        "You are an AI Priority Inbox analyzer. Analyze the provided emails and return a JSON object with 5 keys:\\n"
        "1. important_emails: list of objects {id, reason, priority}. "
        "priority must be 'High', 'Medium', or 'Low'. "
        "Classify emails that need attention (e.g. security notices, account alerts, direct requests, proposals, critical updates). "
        "For marketing or automated newsletters, skip or mark Low. Always explain the concrete reason.\\n"
        "2. action_items: list of objects {task, message_id, deadline, priority, status}. "
        "priority: 'High'|'Medium'|'Low'. status: 'Pending'|'Completed'. "
        "Only extract tasks directly supported by the email text. If no deadline is stated, use 'None explicitly stated'.\\n"
        "3. upcoming_deadlines: list of objects {task, deadline, message_id, status}. "
        "status: 'Upcoming'|'Overdue'|'Unclear'. Only include items with explicit or clearly inferable dates.\\n"
        "4. awaiting_replies: list of objects {message_id, reason}. "
        "Emails from external contacts that contain questions, invitations, or requests needing a response.\\n"
        "5. recommended_follow_ups: list of objects {message_id, reason, suggested_action}. "
        "Conversations where the user would benefit from following up or acknowledging receipt.\\n\\n"
        "STRICT CONSTRAINTS:\\n"
        "- Never invent tasks, deadlines, owners, or IDs.\\n"
        "- Only reference valid message IDs present in the input list.\\n"
        f"- The user's own email is '{user_email}'.\\n"
        "- Return ONLY valid JSON."
    )

    try:
        response = chat_completion_with_retry(
            client,
            model=model_name,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": json.dumps(prompt_data, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return {
            "important_emails": parsed.get("important_emails", []),
            "action_items": parsed.get("action_items", []),
            "upcoming_deadlines": parsed.get("upcoming_deadlines", []),
            "awaiting_replies": parsed.get("awaiting_replies", []),
            "recommended_follow_ups": parsed.get("recommended_follow_ups", []),
        }
    except Exception as error:
        # Graceful degradation: return empty categories on error rather than crashing
        print(f"Warning: classify_emails_for_dashboard encountered error: {error}")
        return empty_result
"""
    ai_code = ai_code.rstrip() + "\n" + classify_def + "\n"
    with open("ai_service.py", "w", encoding="utf-8") as f:
        f.write(ai_code)
    print("Added classify_emails_for_dashboard to ai_service.py")
else:
    print("classify_emails_for_dashboard already present in ai_service.py")
