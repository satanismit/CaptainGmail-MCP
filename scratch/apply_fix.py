import re

# Update gmail_service.py
with open("gmail_service.py", "r", encoding="utf-8") as f:
    gmail_code = f.read()

# 1. Add import re if not present
if "import re" not in gmail_code:
    if "import base64\r\n" in gmail_code:
        gmail_code = gmail_code.replace("import base64\r\n", "import base64\r\nimport re\r\n", 1)
    else:
        gmail_code = gmail_code.replace("import base64\n", "import base64\nimport re\n", 1)

# 2. Add clean_email_body after extract_plain_text
clean_email_body_def = '''

def clean_email_body(body: str, max_chars: int = 1500) -> str:
    """Clean and compact email body to prevent LLM token limit issues."""
    if not body:
        return "(No plain-text body found)"

    cleaned = re.sub(r"\\r\\n|\\r", "\\n", body)
    cleaned = re.sub(r"\\n{3,}", "\\n\\n", cleaned)
    cleaned = re.sub(r"[ \\t]{2,}", " ", cleaned).strip()

    if len(cleaned) > max_chars:
        return (
            cleaned[:max_chars]
            + f"\\n... [Body truncated to {max_chars} chars for context limits]"
        )
    return cleaned
'''

if "def clean_email_body" not in gmail_code:
    target = '    return ""\n\n\ndef list_recent_emails('
    replacement = '    return ""\n' + clean_email_body_def + '\n\ndef list_recent_emails('
    if target not in gmail_code:
        target = '    return ""\r\n\r\n\r\ndef list_recent_emails('
        replacement = '    return ""\r\n' + clean_email_body_def.replace('\n', '\r\n') + '\r\n\r\ndef list_recent_emails('
    assert target in gmail_code, "Target for clean_email_body not found"
    gmail_code = gmail_code.replace(target, replacement, 1)

# 3. Use clean_email_body in get_email
old_get_email = '"body": body or "(No plain-text body found)",'
new_get_email = '"body": clean_email_body(body, max_chars=2000),'
assert old_get_email in gmail_code, "get_email target not found"
gmail_code = gmail_code.replace(old_get_email, new_get_email, 1)

# 4. Use clean_email_body in build_thread
old_build_thread = '"body": body or "(No plain-text body found)",'
new_build_thread = '"body": clean_email_body(body, max_chars=1200),'
assert old_build_thread in gmail_code, "build_thread target not found"
gmail_code = gmail_code.replace(old_build_thread, new_build_thread, 1)

with open("gmail_service.py", "w", encoding="utf-8") as f:
    f.write(gmail_code)
print("gmail_service.py updated successfully")


# Update ai_service.py
with open("ai_service.py", "r", encoding="utf-8") as f:
    ai_code = f.read()

# 1. Update serialize_tool_result to use compact json and max_chars limit
old_serialize = '''def serialize_tool_result(result: Any) -> str:
    """Convert an MCP tool result into text for the model."""

    try:
        return json.dumps(
            result,
            ensure_ascii=False,
        )

    except TypeError as error:
        raise RuntimeError(
            "The MCP tool returned a non-serializable result."
        ) from error'''

new_serialize = '''def serialize_tool_result(result: Any, max_chars: int = 2500) -> str:
    """Convert an MCP tool result into compact text for the model."""

    try:
        text = json.dumps(
            result,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        text = str(result)

    if len(text) > max_chars:
        return (
            text[:max_chars]
            + f"\\n... [Tool result truncated to {max_chars} chars for context limits]"
        )
    return text'''

if old_serialize not in ai_code:
    old_serialize = old_serialize.replace('\n', '\r\n')
    new_serialize = new_serialize.replace('\n', '\r\n')

assert old_serialize in ai_code, "serialize_tool_result not found"
ai_code = ai_code.replace(old_serialize, new_serialize, 1)

# 2. Update chat_completion_with_retry to handle 413 / ITPM token limits
old_retry_except = '''            err_msg = str(error).lower()
            # Catch RateLimitError explicitly or any exception that contains 429 / rate limit
            is_rate_limit = (
                "429" in err_msg
                or "rate limit" in err_msg
                or "too many requests" in err_msg
                or "rate_limit" in type(error).__name__.lower()
            )
            is_tool_use_failed = (
                "tool_use_failed" in err_msg
                or "failed to call a function" in err_msg
            )
            if is_rate_limit:
                if attempt == max_retries - 1:
                    raise error
                delay = base_delay * (2**attempt)
                time.sleep(delay)'''

new_retry_except = '''            err_msg = str(error).lower()
            is_too_large = (
                "413" in err_msg
                or "too large" in err_msg
                or "reduce your message size" in err_msg
                or "itpm" in err_msg
                or "rate_limit_exceeded" in err_msg
            )
            is_rate_limit = (
                "429" in err_msg
                or "rate limit" in err_msg
                or "too many requests" in err_msg
                or "rate_limit" in type(error).__name__.lower()
            )
            is_tool_use_failed = (
                "tool_use_failed" in err_msg
                or "failed to call a function" in err_msg
            )
            if is_too_large and attempt < max_retries - 1:
                # Context limit exceeded: aggressively shrink tool messages and retry
                messages = kwargs.get("messages")
                if isinstance(messages, list):
                    for msg in messages:
                        if msg.get("role") == "tool":
                            content = str(msg.get("content", ""))
                            if len(content) > 400:
                                msg["content"] = content[:400] + "... [truncated due to context limit]"
                        elif msg.get("role") == "assistant" and msg.get("content"):
                            content = str(msg.get("content", ""))
                            if len(content) > 400:
                                msg["content"] = content[:400] + "..."
                time.sleep(2.0)
            elif is_rate_limit:
                if attempt == max_retries - 1:
                    raise error
                delay = base_delay * (2**attempt)
                time.sleep(delay)'''

if old_retry_except not in ai_code:
    old_retry_except = old_retry_except.replace('\n', '\r\n')
    new_retry_except = new_retry_except.replace('\n', '\r\n')

assert old_retry_except in ai_code, "chat_completion_with_retry except block not found"
ai_code = ai_code.replace(old_retry_except, new_retry_except, 1)

# 3. Add sliding window tool pruning in run_iterative_gmail_agent before chat_completion_with_retry
old_while_start = '''    while True:
        response = chat_completion_with_retry('''

new_while_start = '''    while True:
        # Keep accumulated messages well under Groq on-demand limits (~3000 tokens / 10000 chars)
        total_msg_chars = sum(len(str(m.get("content", ""))) for m in messages)
        if total_msg_chars > 10000:
            tool_msgs = [m for m in messages if m.get("role") == "tool"]
            if len(tool_msgs) > 1:
                for old_tool in tool_msgs[:-1]:
                    c = str(old_tool.get("content", ""))
                    if len(c) > 300:
                        old_tool["content"] = c[:300] + "... [earlier tool output condensed]"

        response = chat_completion_with_retry('''

if old_while_start not in ai_code:
    old_while_start = old_while_start.replace('\n', '\r\n')
    new_while_start = new_while_start.replace('\n', '\r\n')

assert old_while_start in ai_code, "while True start not found in ai_service.py"
ai_code = ai_code.replace(old_while_start, new_while_start, 1)

# 4. Guide model to limit thread inspection in action items rule
old_rule_a = '"a. Use search_gmail_threads (e.g. newer_than:7d or a relevant query) to find recent conversations, then get_gmail_thread to retrieve their full content.\\n"'
new_rule_a = '"a. Use search_gmail_threads (e.g. newer_than:7d, max_results=3) to find recent conversations. Inspect up to 2-3 most relevant threads using get_gmail_thread to stay within context limits.\\n"'

if old_rule_a not in ai_code:
    old_rule_a = old_rule_a.replace('\n', '\r\n')
    new_rule_a = new_rule_a.replace('\n', '\r\n')

assert old_rule_a in ai_code, "old_rule_a not found in ai_service.py"
ai_code = ai_code.replace(old_rule_a, new_rule_a, 1)

with open("ai_service.py", "w", encoding="utf-8") as f:
    f.write(ai_code)
print("ai_service.py updated successfully")
