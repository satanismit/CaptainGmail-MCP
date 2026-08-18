# 📧 CAPTAINGMAIL-MCP

An AI-powered Gmail assistant that lets you search, read, summarize, and draft emails using natural language — powered by **Groq LLMs**, the **Model Context Protocol (MCP)**, and a modern **React** chat interface.

---

## ✨ Features

- **Natural Language Chat** — Ask questions about your inbox in plain English ("show me unread emails from GitHub", "summarize the thread with Alice")
- **Iterative AI Agent** — Autonomous multi-step reasoning with up to 5 chained tool calls per request
- **Gmail Search** — Full Gmail query syntax support (`is:unread`, `from:`, `subject:`, `newer_than:7d`, etc.)
- **Email & Thread Reading** — Read individual messages or entire conversation threads in chronological order
- **Inbox Summary** — Aggregated stats: total emails, unread count, top senders
- **Draft Creation** — AI composes drafts with human-in-the-loop confirmation (never auto-sends)
- **Prompt Templates** — 7 built-in templates for common email tasks (professional emails, follow-ups, meeting requests, and more)
- **MCP Tool Server** — Exposes Gmail operations as MCP-compliant tools, usable by any MCP-compatible client
- **Conversation Context** — Maintains chat history for pronoun resolution and follow-up questions
- **Rate Limit Handling** — Exponential backoff with retries for Groq API rate limits
- **Codespaces Ready** — Includes `.devcontainer` configuration for one-click GitHub Codespaces setup

---

## 🏗️ Architecture

```
User (Browser)
    │
    ▼
React UI ─────── frontend/  (port 5173)
    │
    ▼  (HTTP API)
FastAPI ──────── api.py  (port 8000)
    │
    ▼
AI Agent ─────── ai_service.py  ◄──►  Groq LLM API
    │
    ▼
MCP Client ───── mcp_client.py
    │  (stdio subprocess)
    ▼
MCP Server ───── mcp_server.py
    │
    ▼
Gmail Service ── gmail_service.py
    │
    ▼
Gmail API ◄──►── Google OAuth (auth.py)
```

**How it works:**

1. User types a natural language request in the React chat UI
2. React calls `POST /api/chat` on the FastAPI backend
3. `ai_service` sends the request to Groq with available MCP tool definitions
4. Groq selects which Gmail tool(s) to call via function calling
5. `mcp_client` spawns `mcp_server.py` as a subprocess and calls the selected tool
6. `mcp_server` delegates to `gmail_service` functions that interact with the Gmail API
7. For **read** operations, the AI summarizes the results and responds in chat
8. For **write** operations (`create_gmail_draft`), the API returns a `pending_action` and the React UI shows a draft preview for user confirmation
9. User explicitly clicks **"Create Draft"**, which calls `POST /api/draft/create`

---

## 📁 Project Structure

```text
CaptainGmail-MCP/
├── api.py                  # FastAPI backend — REST endpoints
├── ai_service.py           # AI agent — Groq client, tool-calling loop
├── gmail_service.py        # Gmail API operations
├── auth.py                 # Google OAuth2 — token management
├── mcp_server.py           # MCP server — 6 Gmail tools (stdio)
├── mcp_client.py           # MCP client — subprocess communication
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── credentials.json        # Google OAuth client secrets (not committed)
├── token.json              # Cached OAuth token (not committed)
├── .devcontainer/          # GitHub Codespaces / Dev Container config
│
└── frontend/               # React UI (Vite)
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css         # Design system & global styles
        ├── components/
        │   ├── Header.jsx
        │   ├── Sidebar.jsx
        │   ├── ChatArea.jsx
        │   ├── ChatMessage.jsx
        │   ├── ChatInput.jsx
        │   ├── DraftPreview.jsx
        │   └── ToolActivity.jsx
        ├── services/
        │   └── api.js        # Backend API client
        ├── hooks/
        │   └── useChat.js    # Chat state management
        └── data/
            └── templates.js  # 7 prompt templates
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (uses `X | Y` union type syntax)
- **Node.js 18+** and **npm** (for the React frontend)
- A **Google Cloud** project with the Gmail API enabled
- A **Groq** API key ([get one free at console.groq.com](https://console.groq.com))

### 1. Clone the Repository

```bash
git clone https://github.com/satanismit/CaptainGmail-MCP.git
cd CaptainGmail-MCP
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
API_KEY=your_api_key_here
MODEL=llama-3.1-8b-instant
```

### 5. Set Up Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select an existing one)
3. Enable the **Gmail API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Desktop app** as the application type
6. Download the JSON file and save it as `credentials.json` in the project root

> **Alternative:** Set the `GOOGLE_CLIENT_SECRETS_JSON` environment variable with the JSON content instead of saving a file.

### 6. Run the Application

Open two terminals:

**Terminal 1 — Backend:**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser. Click **Connect Gmail** to authenticate via Google OAuth (opens a browser window on first run).

> The Vite dev server proxies all `/api/*` requests to the FastAPI backend on port 8000.

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | **Yes** | API key for your configured LLM provider |
| `MODEL` | **Yes** | Model name (e.g., `llama-3.1-8b-instant`) |
| `GOOGLE_CLIENT_SECRETS_JSON` | One of these **or** a `credentials.json` file | Google OAuth client config as a JSON string |
| `GOOGLE_OAUTH_CLIENT_SECRETS_JSON` | (alternative) | Same as above |
| `GMAIL_CLIENT_SECRETS_JSON` | (alternative) | Same as above |

---

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/status` | Gmail connection status + Groq config check |
| `POST` | `/api/auth/connect` | Trigger Gmail OAuth flow |
| `POST` | `/api/auth/disconnect` | Remove saved Gmail token |
| `GET` | `/api/templates` | Return all 7 prompt templates |
| `POST` | `/api/chat` | Send message → AI agent → response with tool history |
| `POST` | `/api/draft/create` | Create Gmail draft (requires explicit user confirmation) |

Interactive API docs are available at **http://localhost:8000/docs** when the backend is running.

---

## 🔧 MCP Tools

The MCP server exposes 6 Gmail tools that can be used by any MCP-compatible client:

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_gmail` | Search emails with Gmail query syntax | `query`, `max_results` (default: 5) |
| `get_gmail_email` | Retrieve a single email by message ID | `message_id` |
| `search_gmail_threads` | Search Gmail threads/conversations | `query`, `max_results` (default: 5) |
| `get_gmail_thread` | Retrieve a full thread in chronological order | `thread_id` |
| `get_inbox_summary` | Aggregated inbox statistics | `query` (default: `newer_than:1d`), `max_results` (default: 20) |
| `create_gmail_draft` | Create a draft email (does **not** send) | `to`, `subject`, `body` |

### Standalone MCP Server Usage

```bash
python mcp_server.py
```

This starts the server with **stdio** transport, compatible with Claude Desktop, Cursor, or any MCP client.

---

## 📝 Prompt Templates

The sidebar includes 7 ready-to-use prompt templates:

| Template | Use Case |
|----------|----------|
| **Professional new message** | Compose a formal email with a call to action |
| **Reply to message (by ID)** | Reply to a specific email using its message ID |
| **Follow-up** | Send a polite status-update request |
| **Summarize thread into reply** | Summarize a conversation and draft a response |
| **Meeting / schedule request** | Propose a meeting with agenda and time options |
| **Casual short** | Quick, informal note under 50 words |
| **Return JSON draft (tool)** | Get a structured JSON draft for programmatic use |

Templates can be selected from the sidebar, edited in the text area, and then sent into chat or copied to clipboard.

---

## 🔒 Human-in-the-Loop Draft Creation

Draft creation follows a strict confirmation flow:

```
User selects template / types request
        ↓
AI generates draft via Groq
        ↓
Backend returns pending_action (NOT created yet)
        ↓
React shows draft preview (To, Subject, Body)
        ↓
User explicitly clicks "Create Draft"
        ↓
React calls POST /api/draft/create
        ↓
Backend creates Gmail draft via API
```

**The AI can never automatically create or send a Gmail draft.** Every write operation requires explicit user confirmation through the UI.

---

## 🔒 Security

- **OAuth tokens** (`token.json`) and **client secrets** (`credentials.json`) are excluded from version control via `.gitignore`
- **Draft-only writes** — The AI can only create drafts, never send emails automatically
- **Human-in-the-loop** — All draft creation requires explicit user confirmation
- **Server-side credentials** — OAuth tokens and API keys never leave the Python backend; the React frontend only communicates via REST API
- **Gmail scopes** are limited to `gmail.readonly` and `gmail.compose`
- **CORS** restricted to `localhost:5173` in development

---

## 🐳 GitHub Codespaces / Dev Container

This project includes a `.devcontainer` configuration for instant setup:

- **Base image:** Python 3.11 (Debian Bookworm)
- **Node.js 20** included for the React frontend
- **Auto-installs** all Python and npm dependencies
- **Auto-starts** both FastAPI (port 8000) and Vite dev server (port 5173)
- **VS Code extensions:** Python, Pylance

To use: open the repo in GitHub Codespaces or VS Code Dev Containers. Both services start automatically.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a Pull Request with a description of the change

---

## 📄 License

No license specified. Add a `LICENSE` file if you want to set one.
