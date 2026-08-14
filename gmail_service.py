import base64
from email.message import EmailMessage
from typing import Any


from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import authenticate_gmail


def build_gmail_service(
    access_token: str | None = None,
) -> Any:
    """Create and return an authenticated Gmail API service."""

    cleaned_access_token = (
        access_token.strip()
        if access_token
        else ""
    )

    if cleaned_access_token:
        credentials = Credentials(
            token=cleaned_access_token,
            scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.compose",
            ],
        )
    else:
        credentials = authenticate_gmail()

    return build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )


def get_header(headers: list[dict[str, str]], name: str) -> str:
    """Return a specific email header value."""

    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


def decode_base64url(data: str) -> str:
    """Decode Gmail Base64URL data into readable UTF-8 text."""

    if not data:
        return ""

    try:
        decoded_bytes = base64.urlsafe_b64decode(
            data + "=" * (-len(data) % 4)
        )

        return decoded_bytes.decode(
            "utf-8",
            errors="replace",
        )

    except (ValueError, TypeError) as error:
        raise ValueError(
            "Unable to decode the email body."
        ) from error


def extract_plain_text(part: dict[str, Any]) -> str:
    """Recursively extract the plain-text body from a Gmail MIME part."""

    mime_type = part.get("mimeType", "")
    body = part.get("body", {})
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return decode_base64url(data).strip()

    for child_part in part.get("parts", []):
        text = extract_plain_text(child_part)

        if text:
            return text

    return ""


def list_recent_emails(
    max_results: int = 5,
    access_token: str | None = None,
) -> list[dict[str, str]]:
    """Return basic details for recent inbox emails."""

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    service = build_gmail_service(access_token=access_token)

    try:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=max_results,
            )
            .execute()
        )

        messages = response.get("messages", [])
        results: list[dict[str, str]] = []

        for message in messages:
            message_id = message["id"]

            message_data = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )

            headers = message_data.get("payload", {}).get("headers", [])

            results.append(
                {
                    "id": message_id,
                    "sender": get_header(headers, "From"),
                    "subject": get_header(headers, "Subject") or "(No subject)",
                    "date": get_header(headers, "Date"),
                }
            )

        return results

    except HttpError as error:
        raise RuntimeError(
            f"Gmail API request failed: {error}"
        ) from error


def search_emails(
    query: str,
    max_results: int = 10,
    access_token: str | None = None,
) -> list[dict[str, str]]:
    """Search Gmail and return metadata for matching emails."""

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    service = build_gmail_service(access_token=access_token)

    try:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=cleaned_query,
                maxResults=max_results,
            )
            .execute()
        )

        messages = response.get("messages", [])
        results: list[dict[str, str]] = []

        for message in messages:
            message_id = message["id"]

            message_data = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )

            headers = message_data.get("payload", {}).get("headers", [])

            results.append(
                {
                    "id": message_id,
                    "sender": get_header(headers, "From"),
                    "subject": get_header(headers, "Subject") or "(No subject)",
                    "date": get_header(headers, "Date"),
                }
            )

        return results

    except HttpError as error:
        raise RuntimeError(
            f"Gmail search request failed: {error}"
        ) from error


def get_email(
    message_id: str,
    access_token: str | None = None,
) -> dict[str, str]:
    """Return metadata and plain-text content for one Gmail message."""

    cleaned_message_id = message_id.strip()

    if not cleaned_message_id:
        raise ValueError("message_id cannot be empty.")

    service = build_gmail_service(access_token=access_token)

    try:
        message_data = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=cleaned_message_id,
                format="full",
            )
            .execute()
        )

        payload = message_data.get("payload", {})
        headers = payload.get("headers", [])

        body = extract_plain_text(payload)

        return {
            "id": message_data.get("id", cleaned_message_id),
            "thread_id": message_data.get("threadId", ""),
            "sender": get_header(headers, "From"),
            "recipient": get_header(headers, "To"),
            "subject": get_header(headers, "Subject") or "(No subject)",
            "date": get_header(headers, "Date"),
            "body": body or "(No plain-text body found)",
        }

    except HttpError as error:
        raise RuntimeError(
            f"Unable to retrieve Gmail message: {error}"
        ) from error


def build_thread_metadata(
    thread_data: dict[str, Any],
) -> dict[str, Any]:
    """Build lightweight metadata for one Gmail thread."""

    messages = thread_data.get("messages", [])

    if not messages:
        return {
            "thread_id": thread_data.get("id", ""),
            "subject": "(No subject)",
            "participants": [],
            "message_count": 0,
            "latest_date": "",
            "snippet": thread_data.get("snippet", ""),
        }

    participants: list[str] = []
    subject = "(No subject)"
    latest_date = ""

    for message in messages:
        headers = (
            message.get("payload", {})
            .get("headers", [])
        )

        sender = get_header(headers, "From")

        if sender and sender not in participants:
            participants.append(sender)

        current_subject = get_header(
            headers,
            "Subject",
        )

        if (
            subject == "(No subject)"
            and current_subject
        ):
            subject = current_subject

        current_date = get_header(
            headers,
            "Date",
        )

        if current_date:
            latest_date = current_date

    return {
        "thread_id": thread_data.get("id", ""),
        "subject": subject,
        "participants": participants,
        "message_count": len(messages),
        "latest_date": latest_date,
        "snippet": thread_data.get("snippet", ""),
    }


def search_threads(
    query: str,
    max_results: int = 5,
    access_token: str | None = None,
) -> list[dict[str, Any]]:
    """Search Gmail threads and return lightweight metadata."""

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if max_results < 1:
        raise ValueError(
            "max_results must be at least 1."
        )

    if max_results > 20:
        raise ValueError(
            "max_results cannot exceed 20."
        )

    service = build_gmail_service(
        access_token=access_token
    )

    try:
        response = (
            service.users()
            .threads()
            .list(
                userId="me",
                q=cleaned_query,
                maxResults=max_results,
            )
            .execute()
        )

        threads = response.get("threads", [])
        results: list[dict[str, Any]] = []

        for thread in threads:
            thread_id = thread["id"]

            thread_data = (
                service.users()
                .threads()
                .get(
                    userId="me",
                    id=thread_id,
                    format="metadata",
                    metadataHeaders=[
                        "From",
                        "Subject",
                        "Date",
                    ],
                )
                .execute()
            )

            results.append(
                build_thread_metadata(
                    thread_data
                )
            )

        return results

    except HttpError as error:
        raise RuntimeError(
            f"Gmail thread search failed: {error}"
        ) from error


def get_thread(
    thread_id: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Retrieve raw Gmail thread response by ID."""

    cleaned_thread_id = thread_id.strip()

    if not cleaned_thread_id:
        raise ValueError("thread_id cannot be empty.")

    service = build_gmail_service(access_token=access_token)

    try:
        response = (
            service.users()
            .threads()
            .get(
                userId="me",
                id=cleaned_thread_id,
                format="full",
            )
            .execute()
        )
        return response

    except HttpError as error:
        raise RuntimeError(
            f"Gmail thread retrieval failed: {error}"
        ) from error


def build_thread(
    thread_data: dict[str, Any],
) -> dict[str, Any]:
    """Build structured, chronological thread metadata from raw Gmail response."""

    messages = thread_data.get("messages", [])
    thread_id = thread_data.get("id", "")

    # Sort messages chronologically by internalDate (Gmail internal timestamp)
    try:
        sorted_messages = sorted(
            messages,
            key=lambda m: int(m.get("internalDate", "0")),
        )
    except (ValueError, TypeError):
        sorted_messages = messages

    built_messages: list[dict[str, Any]] = []
    subject = "(No subject)"

    for message in sorted_messages:
        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        current_subject = get_header(headers, "Subject")
        if subject == "(No subject)" and current_subject:
            subject = current_subject

        body = extract_plain_text(payload)

        built_messages.append(
            {
                "message_id": message.get("id", ""),
                "sender": get_header(headers, "From"),
                "recipient": get_header(headers, "To"),
                "date": get_header(headers, "Date"),
                "body": body or "(No plain-text body found)",
            }
        )

    return {
        "thread_id": thread_id,
        "subject": subject,
        "message_count": len(built_messages),
        "messages": built_messages,
    }


def extract_sender_name(sender_raw: str) -> str:
    """Extract a clean sender display name from raw From header value."""

    if not sender_raw:
        return "Unknown"

    if "<" in sender_raw:
        name_part = sender_raw.split("<")[0].strip()
        if name_part.startswith('"') and name_part.endswith('"'):
            name_part = name_part[1:-1].strip()
        if name_part:
            return name_part

    return sender_raw.strip()


def get_inbox_summary(
    query: str = "newer_than:1d",
    max_results: int = 20,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Retrieve a structured summary of recent inbox activity."""

    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("query cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    if max_results > 50:
        raise ValueError("max_results cannot exceed 50.")

    # Fetch total matching emails
    total_list = search_emails(
        query=cleaned_query,
        max_results=max_results,
        access_token=access_token,
    )

    # Fetch unread matching emails
    unread_query = f"{cleaned_query} is:unread"
    unread_list = search_emails(
        query=unread_query,
        max_results=max_results,
        access_token=access_token,
    )

    # Build sender frequency
    sender_counts: dict[str, int] = {}
    for email in total_list:
        raw_sender = email.get("sender", "")
        sender_name = extract_sender_name(raw_sender)
        sender_counts[sender_name] = (
            sender_counts.get(sender_name, 0) + 1
        )

    # Sort descending by count, then alphabetically
    sorted_senders = sorted(
        sender_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    senders_ranking = [
        {"sender": k, "count": v}
        for k, v in sorted_senders[:5]
    ]

    # Map to lightweight metadata
    lightweight_emails = [
        {
            "subject": e.get("subject", ""),
            "sender": e.get("sender", ""),
            "date": e.get("date", ""),
        }
        for e in total_list
    ]

    return {
        "total_emails": len(total_list),
        "unread": len(unread_list),
        "senders": senders_ranking,
        "emails": lightweight_emails,
    }


def build_email_message(
    to: str,
    subject: str,
    body: str,
) -> str:
    """Build a Gmail API-compatible encoded email message."""

    cleaned_to = to.strip()
    cleaned_subject = subject.strip()
    cleaned_body = body.strip()

    if not cleaned_to:
        raise ValueError("to cannot be empty.")

    if not cleaned_subject:
        raise ValueError("subject cannot be empty.")

    if not cleaned_body:
        raise ValueError("body cannot be empty.")

    message = EmailMessage()

    message["To"] = cleaned_to
    message["Subject"] = cleaned_subject

    message.set_content(cleaned_body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    return encoded_message


def create_draft(
    to: str,
    subject: str,
    body: str,
    access_token: str | None = None,
) -> dict[str, str]:
    """Create a Gmail draft without sending it."""

    service = build_gmail_service(
        access_token=access_token
    )

    raw_message = build_email_message(
        to=to,
        subject=subject,
        body=body,
    )

    try:
        response = (
            service.users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {
                        "raw": raw_message,
                    }
                },
            )
            .execute()
        )

        message = response.get("message", {})

        return {
            "draft_id": response.get("id", ""),
            "message_id": message.get("id", ""),
            "thread_id": message.get(
                "threadId",
                "",
            ),
            "status": "draft_created",
        }

    except HttpError as error:
        raise RuntimeError(
            f"Unable to create Gmail draft: {error}"
        ) from error






