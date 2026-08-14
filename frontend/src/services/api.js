const API_BASE = '';

async function handleResponse(response) {
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) {
        detail = data.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function getStatus() {
  const response = await fetch(`${API_BASE}/api/status`);
  return handleResponse(response);
}

export async function connectGmail() {
  const response = await fetch(`${API_BASE}/api/auth/connect`, {
    method: 'POST',
  });
  return handleResponse(response);
}

export async function disconnectGmail() {
  const response = await fetch(`${API_BASE}/api/auth/disconnect`, {
    method: 'POST',
  });
  return handleResponse(response);
}

export async function getTemplates() {
  const response = await fetch(`${API_BASE}/api/templates`);
  return handleResponse(response);
}

export async function sendChatMessage(message, conversationHistory) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory,
    }),
  });
  return handleResponse(response);
}

export async function createDraft(to, subject, body) {
  const response = await fetch(`${API_BASE}/api/draft/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ to, subject, body }),
  });
  return handleResponse(response);
}
