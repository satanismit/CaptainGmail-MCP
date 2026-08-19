import { useState } from 'react';
import { User, Bot, Trash2, Pencil, RotateCcw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ToolActivity from './ToolActivity';

function ChatMessage({ message, onDelete, onEdit, onRegenerate }) {
  const { id, role, content, isError, toolHistory } = message;
  const isUser = role === 'user';
  const isSystem = role === 'system';

  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(content);

  // System messages just return styled text, no actions or avatar
  if (isSystem) {
    return (
      <div className="chat-message-wrapper chat-message-wrapper--system">
        <div className="chat-message">
          <div className="chat-message__body">
            <div className="chat-message__bubble">
              {content}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const handleEditSave = () => {
    if (editValue.trim() !== content) {
      onEdit(id, editValue);
    }
    setIsEditing(false);
  };

  let wrapperClass = 'chat-message-wrapper';
  if (isUser) wrapperClass += ' chat-message-wrapper--user';
  else wrapperClass += ' chat-message-wrapper--assistant';
  if (isError) wrapperClass += ' chat-message-wrapper--error';

  return (
    <div className={wrapperClass}>
      <div className="chat-message">
        <div className="chat-message__avatar">
          {isUser ? <User /> : <Bot />}
        </div>
        <div className="chat-message__body">
          {isEditing ? (
            <div style={{ width: '100%' }}>
              <textarea
                className="chat-message__edit-area"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                autoFocus
              />
              <div className="chat-message__edit-actions">
                <button
                  className="btn btn--secondary btn--small"
                  onClick={() => setIsEditing(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn--primary btn--small"
                  onClick={handleEditSave}
                >
                  Save & Resend
                </button>
              </div>
            </div>
          ) : (
            <div className="chat-message__bubble">
              {isUser ? (
                content
              ) : (
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          )}

          {toolHistory && toolHistory.length > 0 && (
            <ToolActivity toolHistory={toolHistory} />
          )}

          {isDeleting && (
            <div className="chat-message__delete-confirm">
              <span>Delete this message?</span>
              <div className="chat-message__delete-actions">
                <button 
                  className="btn btn--ghost btn--small"
                  onClick={() => setIsDeleting(false)}
                >
                  Cancel
                </button>
                <button 
                  className="btn btn--danger btn--small"
                  onClick={() => onDelete(id)}
                >
                  Confirm
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Desktop Hover Actions */}
        {!isEditing && !isDeleting && (
          <div className="chat-message__actions">
            {isUser && (
              <button 
                className="chat-message__action-btn chat-message__action-btn--edit"
                onClick={() => {
                  setEditValue(content);
                  setIsEditing(true);
                }}
                title="Edit message"
              >
                <Pencil size={14} />
              </button>
            )}
            {!isUser && !isError && (
              <button 
                className="chat-message__action-btn chat-message__action-btn--regen"
                onClick={() => onRegenerate(id)}
                title="Regenerate response"
              >
                <RotateCcw size={14} />
              </button>
            )}
            <button 
              className="chat-message__action-btn chat-message__action-btn--delete"
              onClick={() => setIsDeleting(true)}
              title="Delete message"
            >
              <Trash2 size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
