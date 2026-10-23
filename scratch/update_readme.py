with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

old_features = """## ✨ Features

- **Natural Language Chat"""

new_features = """## ✨ Features

- **AI Priority Inbox Dashboard** — Unified dashboard displaying Important Emails, Pending Action Items, Upcoming Deadlines, Awaiting Replies, and Recommended Follow-ups with real-time summary cards and one-click actions
- **Natural Language Chat"""

if old_features in readme:
    readme = readme.replace(old_features, new_features, 1)

# Add dashboard documentation section before Quick Start
dashboard_doc = """
## 📊 AI Priority Inbox Dashboard

Access the **Dashboard** toggle in the header navigation to view an intelligent breakdown of your inbox:

- **Summary Cards**: Real-time counts of Important Emails, Pending Actions, Upcoming Deadlines, and Awaiting Replies.
- **Important Emails**: Filtered and classified with priority badges (High, Medium, Low) and AI explanations grounded in email content.
- **Pending Action Items**: Extracted tasks with source email references, explicit deadlines, and status indicators.
- **Upcoming Deadlines**: Commitments with due dates and overdue/upcoming status.
- **Awaiting Replies**: Conversations where the other participant asked a question or is waiting for response.
- **Recommended Follow-ups**: Proactive suggestions with a one-click **Draft Follow-up** action that launches the existing tone-controlled draft composer.
- **Refresh Action**: On-demand sync with Gmail API and Groq analysis.

"""

if "## 🚀 Quick Start" in readme:
    readme = readme.replace("## 🚀 Quick Start", dashboard_doc + "## 🚀 Quick Start", 1)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
print("README.md updated successfully")
