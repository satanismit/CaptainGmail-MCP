import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from gmail_service import (
    build_thread,
    create_draft,
    get_email,
    get_inbox_summary as get_inbox_summary_impl,
    get_thread,
    search_emails,
    search_threads,
)


mcp = FastMCP("CAPTAINGMAIL-MCP Gmail MCP")


def get_request_access_token() -> str | None:
    """Return the web user's Gmail token from the server environment."""

    access_token = os.getenv(
        "CAPTAINGMAIL_GMAIL_ACCESS_TOKEN",
        "",
    ).strip()

    return access_token or None


@mcp.tool()
def search_gmail(
    query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """
    Search the authenticated user's Gmail account.

    Use Gmail search syntax such as:
    - is:unread
    - from:github.com
    - subject:interview
    - newer_than:7d

    Args:
        query: Gmail search query.
        max_results: Maximum number of matching emails to return.

    Returns:
        Matching email metadata containing message ID, sender,
        subject and date.
    """

    return search_emails(
        query=query,
        max_results=max_results,
        access_token=get_request_access_token(),
    )


@mcp.tool()
def search_gmail_messages(
    query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """
    Search the authenticated user's Gmail messages.

    Use Gmail search syntax such as:
    - is:unread
    - from:github.com
    - subject:interview
    - newer_than:7d

    Args:
        query: Gmail search query.
        max_results: Maximum number of matching emails to return.

    Returns:
        Matching email metadata containing message ID, sender,
        subject and date.
    """

    return search_emails(
        query=query,
        max_results=max_results,
        access_token=get_request_access_token(),
    )


@mcp.tool()
def get_gmail_email(
    message_id: str,
) -> dict[str, Any]:
    """
    Retrieve one Gmail message using its message ID.

    Use this tool after search_gmail returns a message ID.

    Args:
        message_id: Gmail message ID returned by search_gmail.

    Returns:
        Email details containing the message ID, thread ID, sender,
        recipient, subject, date and plain-text body.
    """

    return get_email(
        message_id=message_id,
        access_token=get_request_access_token(),
    )


@mcp.tool()
def get_gmail_message(
    message_id: str,
) -> dict[str, Any]:
    """
    Retrieve one Gmail message using its message ID.

    Args:
        message_id: Gmail message ID.

    Returns:
        Email details containing the message ID, thread ID, sender,
        recipient, subject, date and plain-text body.
    """

    return get_email(
        message_id=message_id,
        access_token=get_request_access_token(),
    )


@mcp.tool()
def search_gmail_threads(
    query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """
    Search Gmail conversations using Gmail search syntax.

    Args:
        query: Gmail search query such as
            from:example.com or newer_than:7d.
        max_results: Maximum number of threads to return.

    Returns:
        Thread metadata including thread ID, subject,
        participants, message count, latest date and snippet.
    """

    return search_threads(
        query=query,
        max_results=max_results,
        access_token=get_request_access_token(),
    )


@mcp.tool()
def get_gmail_thread(
    thread_id: str,
) -> dict[str, Any]:
    """
    Retrieve a complete Gmail thread (conversation) in chronological order.

    Use this tool after search_gmail_threads returns a thread ID.

    Args:
        thread_id: Gmail thread ID.

    Returns:
        Thread details containing thread ID, subject, message count,
        and chronological list of messages with message ID, sender,
        recipient, date and plain-text body.
    """

    raw_thread = get_thread(
        thread_id=thread_id,
        access_token=get_request_access_token(),
    )
    return build_thread(raw_thread)


@mcp.tool()
def get_inbox_summary(
    query: str = "newer_than:1d",
    max_results: int = 20,
) -> dict[str, Any]:
    """
    Retrieve a structured, aggregated summary of recent Gmail inbox activity.

    Do not use this to read specific email contents. Use it to understand
    overall statistics, active senders, and recent email metadata.

    Args:
        query: Gmail search query such as newer_than:1d.
        max_results: Maximum number of recent emails to aggregate.

    Returns:
        Structured inbox data with total_emails, unread count,
        top senders, and a list of lightweight email metadata.
    """

    return get_inbox_summary_impl(
        query=query,
        max_results=max_results,
        access_token=get_request_access_token(),
    )


@mcp.tool()
def create_gmail_draft(
    to: str,
    subject: str,
    body: str,
) -> dict[str, str]:
    """
    Create a Gmail draft without sending it.

    This tool should only be executed after explicit user confirmation.

    Args:
        to: Recipient email address.
        subject: Draft email subject.
        body: Plain-text email body.

    Returns:
        Draft ID, message ID, thread ID and creation status.
    """

    return create_draft(
        to=to,
        subject=subject,
        body=body,
        access_token=get_request_access_token(),
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
