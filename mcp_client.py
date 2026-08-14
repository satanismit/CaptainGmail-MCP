import json
import os
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_DIR = Path(__file__).resolve().parent
SERVER_FILE = PROJECT_DIR / "mcp_server.py"

SessionCallback = Callable[
    [ClientSession],
    Awaitable[Any],
]


def extract_text_content(result: Any) -> list[str]:
    """Extract all text blocks from an MCP tool result."""

    return [
        content.text
        for content in result.content
        if content.type == "text"
    ]


def parse_tool_result(result: Any) -> Any:
    """Parse an MCP tool result into normal Python data."""

    text_blocks = extract_text_content(result)

    if not text_blocks:
        raise RuntimeError(
            "The MCP tool returned no text content."
        )

    if result.isError:
        raise RuntimeError("\n".join(text_blocks))

    if len(text_blocks) == 1:
        try:
            return json.loads(text_blocks[0])
        except json.JSONDecodeError:
            return text_blocks[0]

    parsed_items: list[Any] = []

    for text in text_blocks:
        try:
            parsed_items.append(json.loads(text))
        except json.JSONDecodeError:
            parsed_items.append(text)

    return parsed_items


async def run_with_mcp_session(
    callback: SessionCallback,
    access_token: str | None = None,
) -> Any:
    """Start the MCP server and run a callback with an initialized session."""

    server_environment = os.environ.copy()

    cleaned_access_token = (
        access_token.strip()
        if access_token
        else ""
    )

    if cleaned_access_token:
        server_environment[
            "CAPTAINGMAIL_GMAIL_ACCESS_TOKEN"
        ] = cleaned_access_token
    else:
        server_environment.pop(
            "CAPTAINGMAIL_GMAIL_ACCESS_TOKEN",
            None,
        )

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
        cwd=str(PROJECT_DIR),
        env=server_environment,
    )

    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()

            return await callback(session)


async def list_mcp_tools() -> list[dict[str, Any]]:
    """Return the tools exposed by the CAPTAINGMAIL-MCP server."""

    async def operation(
        session: ClientSession,
    ) -> list[dict[str, Any]]:
        response = await session.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    return await run_with_mcp_session(operation)


async def call_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    access_token: str | None = None,
) -> Any:
    """Call a CAPTAINGMAIL-MCP tool and return parsed Python data."""

    cleaned_tool_name = tool_name.strip()

    if not cleaned_tool_name:
        raise ValueError("tool_name cannot be empty.")

    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a dictionary.")

    async def operation(session: ClientSession) -> Any:
        result = await session.call_tool(
            cleaned_tool_name,
            arguments=arguments,
        )

        return parse_tool_result(result)

    return await run_with_mcp_session(
        operation,
        access_token=access_token,
    )
