import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from mcp_client import call_mcp_tool, list_mcp_tools


load_dotenv()


def get_groq_client() -> Groq:
    """Create a Groq client using the configured API key."""

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    return Groq(api_key=api_key)


def get_model_name() -> str:
    """Return the configured Groq model name."""

    model_name = os.getenv("GROQ_MODEL", "").strip()

    if not model_name:
        raise RuntimeError(
            "GROQ_MODEL is not configured."
        )

    return model_name


def chat_completion_with_retry(client: Groq, **kwargs: Any) -> Any:
    """Execute Groq chat completion with exponential backoff on rate limits."""

    max_retries = 5
    base_delay = 2.0

    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as error:
            err_msg = str(error).lower()
            # Catch RateLimitError explicitly or any exception that contains 429 / rate limit
            is_rate_limit = (
                "429" in err_msg
                or "rate limit" in err_msg
                or "too many requests" in err_msg
                or "rate_limit" in type(error).__name__.lower()
            )
            if is_rate_limit:
                if attempt == max_retries - 1:
                    raise error
                delay = base_delay * (2**attempt)
                time.sleep(delay)
            else:
                raise error


def generate_text(prompt: str) -> str:
    """Generate a text response using Groq."""

    cleaned_prompt = prompt.strip()

    if not cleaned_prompt:
        raise ValueError("prompt cannot be empty.")

    client = get_groq_client()
    model_name = get_model_name()

    chat_completion = chat_completion_with_retry(
        client,
        messages=[
            {
                "role": "user",
                "content": cleaned_prompt,
            }
        ],
        model=model_name,
    )

    response_text = chat_completion.choices[0].message.content

    if not response_text:
        raise RuntimeError(
            "Groq returned no text response."
        )

    return response_text.strip()


def convert_mcp_tools_to_groq(
    mcp_tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert MCP tool definitions into Groq function tools."""

    groq_tools: list[dict[str, Any]] = []

    for tool in mcp_tools:
        groq_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
        )

    return groq_tools


async def select_gmail_tool(
    user_request: str,
) -> dict[str, Any]:
    """Ask Groq to select an appropriate Gmail MCP tool."""

    cleaned_request = user_request.strip()

    if not cleaned_request:
        raise ValueError("user_request cannot be empty.")

    mcp_tools = await list_mcp_tools()
    groq_tools = convert_mcp_tools_to_groq(mcp_tools)

    client = get_groq_client()
    model_name = get_model_name()

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an email assistant. "
                    "Use the available Gmail tools when the user asks "
                    "to search, find, list, or read Gmail messages. "
                    "Do not invent message IDs."
                ),
            },
            {
                "role": "user",
                "content": cleaned_request,
            },
        ],
        tools=groq_tools,
        tool_choice="auto",
        temperature=0,
    )

    message = response.choices[0].message

    if not message.tool_calls:
        return {
            "type": "text",
            "content": message.content or "",
        }

    tool_call = message.tool_calls[0]

    try:
        arguments = json.loads(
            tool_call.function.arguments
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Groq returned invalid tool arguments."
        ) from error

    return {
        "type": "tool_call",
        "tool_call_id": tool_call.id,
        "tool_name": tool_call.function.name,
        "arguments": arguments,
    }


def validate_selected_tool(
    tool_name: str,
    available_tools: list[dict[str, Any]],
) -> None:
    """Confirm that the model selected a discovered MCP tool."""

    allowed_names = {
        tool["name"]
        for tool in available_tools
    }

    if tool_name not in allowed_names:
        raise RuntimeError(
            f"Groq selected an unknown tool: {tool_name}"
        )


def serialize_tool_result(result: Any) -> str:
    """Convert an MCP tool result into text for the model."""

    try:
        return json.dumps(
            result,
            ensure_ascii=False,
        )

    except TypeError as error:
        raise RuntimeError(
            "The MCP tool returned a non-serializable result."
        ) from error


async def run_gmail_agent(
    user_request: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Select, execute and summarize a Gmail MCP tool call."""

    cleaned_request = user_request.strip()

    if not cleaned_request:
        raise ValueError("user_request cannot be empty.")

    mcp_tools = await list_mcp_tools()
    groq_tools = convert_mcp_tools_to_groq(mcp_tools)

    client = get_groq_client()
    model_name = get_model_name()

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are CAPTAINGMAIL-MCP, a Gmail assistant. "
                "Use the available tools when Gmail data is needed. "
                "Never invent email details or message IDs. "
                "After receiving a tool result, summarize it clearly. "
                "Do not claim an action succeeded unless the tool "
                "result confirms it."
            ),
        },
        {
            "role": "user",
            "content": cleaned_request,
        },
    ]

    first_response = chat_completion_with_retry(
        client,
        model=model_name,
        messages=messages,
        tools=groq_tools,
        tool_choice="auto",
        temperature=0,
    )

    assistant_message = first_response.choices[0].message

    if not assistant_message.tool_calls:
        return {
            "answer": assistant_message.content or "",
            "tool_used": None,
            "tool_arguments": None,
        }

    tool_call = assistant_message.tool_calls[0]
    tool_name = tool_call.function.name

    validate_selected_tool(
        tool_name=tool_name,
        available_tools=mcp_tools,
    )

    try:
        tool_arguments = json.loads(
            tool_call.function.arguments
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Groq returned invalid tool arguments."
        ) from error

    if not isinstance(tool_arguments, dict):
        raise RuntimeError(
            "Groq tool arguments must be a JSON object."
        )

    tool_result = await call_mcp_tool(
        tool_name=tool_name,
        arguments=tool_arguments,
        access_token=access_token,
    )

    serialized_result = serialize_tool_result(
        tool_result
    )

    messages.append(
        {
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": (
                            tool_call.function.arguments
                        ),
                    },
                }
            ],
        }
    )

    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_name,
            "content": serialized_result,
        }
    )

    final_response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=groq_tools,
        tool_choice="none",
        temperature=0,
    )

    final_message = final_response.choices[0].message

    if not final_message.content:
        raise RuntimeError(
            "Groq returned no final answer."
        )

    return {
        "answer": final_message.content.strip(),
        "tool_used": tool_name,
        "tool_arguments": tool_arguments,
    }


def prepare_conversation_history(
    conversation_history: list[dict[str, str]] | None,
    max_messages: int = 10,
) -> list[dict[str, str]]:
    """Validate and limit conversation history for the model."""

    if conversation_history is None:
        return []

    if not isinstance(conversation_history, list):
        raise TypeError(
            "conversation_history must be a list."
        )

    prepared_messages: list[dict[str, str]] = []

    for message in conversation_history[-max_messages:]:
        if not isinstance(message, dict):
            continue

        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()

        if role not in {"user", "assistant"}:
            continue

        if not content:
            continue

        prepared_messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    return prepared_messages


WRITE_TOOLS = {
    "create_gmail_draft",
}


async def run_iterative_gmail_agent(
    user_request: str,
    conversation_history: list[dict[str, str]] | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Autonomous iterative Gmail agent that loops reasoning and tool calls with context."""

    cleaned_request = user_request.strip()

    if not cleaned_request:
        raise ValueError("user_request cannot be empty.")

    mcp_tools = await list_mcp_tools()
    groq_tools = convert_mcp_tools_to_groq(mcp_tools)

    client = get_groq_client()
    model_name = get_model_name()

    history = prepare_conversation_history(
        conversation_history
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are CAPTAINGMAIL-MCP, a Gmail assistant.\n"
                "Follow these instructions:\n"
                "1. Use Gmail tools whenever private Gmail data is needed.\n"
                "2. For requests about conversations or threads (e.g. 'conversation with X', 'thread about Y'), use the thread tools: search_gmail_threads and get_gmail_thread.\n"
                "3. For requests about individual emails or messages, use the message tools: search_gmail and get_gmail_email.\n"
                "4. Use the recent conversation history to understand references such as 'it', 'that email', 'the thread', or 'the previous one'. Use any message IDs or thread IDs present in the history directly instead of searching for them again.\n"
                "5. Never invent email details or message IDs.\n"
                "6. After receiving tool results, answer clearly and only using information supported by those results.\n"
                "7. When replying to an email, sender, or conversation, you MUST first search for the email or thread to find the correct recipient email address and subject. Never guess or invent recipient addresses or subjects."
            ),
        },
        *history,
        {
            "role": "user",
            "content": cleaned_request,
        },
    ]

    tool_history: list[dict[str, Any]] = []
    total_tool_calls = 0
    MAX_TOOL_CALLS = 5

    while True:
        response = chat_completion_with_retry(
            client,
            model=model_name,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
            temperature=0,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            final_content = message.content or ""
            break

        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name

        validate_selected_tool(
            tool_name=tool_name,
            available_tools=mcp_tools,
        )

        try:
            tool_arguments = json.loads(
                tool_call.function.arguments
            )
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Groq returned invalid tool arguments."
            ) from error

        if not isinstance(tool_arguments, dict):
            raise RuntimeError(
                "Groq tool arguments must be a JSON object."
            )

        if tool_name in WRITE_TOOLS:
            return {
                "answer": "",
                "tool_history": tool_history,
                "total_tool_calls": total_tool_calls,
                "pending_action": {
                    "tool_name": tool_name,
                    "arguments": tool_arguments,
                },
            }

        if total_tool_calls >= MAX_TOOL_CALLS:
            raise RuntimeError("Maximum tool calls exceeded.")

        tool_result = await call_mcp_tool(
            tool_name=tool_name,
            arguments=tool_arguments,
            access_token=access_token,
        )
        total_tool_calls += 1

        serialized_result = serialize_tool_result(
            tool_result
        )

        tool_history.append(
            {
                "tool_name": tool_name,
                "arguments": tool_arguments,
                "result": tool_result,
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": (
                                tool_call.function.arguments
                            ),
                        },
                    }
                ],
            }
        )

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": serialized_result,
            }
        )

    return {
        "answer": final_content.strip(),
        "tool_history": tool_history,
        "total_tool_calls": total_tool_calls,
        "pending_action": None,
    }

