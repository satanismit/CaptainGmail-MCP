import { MessageSquare, Bot } from 'lucide-react';
import ChatMessage from './ChatMessage';

function ChatArea({ messages, isLoading, onDelete, onEdit, onRegenerate }) {
  if (messages.length === 0) {
    return (
      <div className="chat-area">
        <div className="chat-area__empty">
          <div className="chat-area__empty-icon">
            <Bot />
          </div>
          <p className="chat-area__empty-text">
            I'm CaptainGmail-MCP. Ask me to search your inbox, summarize threads, or draft replies.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-area">
      {messages.map((msg, idx) => (
        <ChatMessage 
          key={msg.id || idx} 
          message={msg} 
          onDelete={onDelete}
          onEdit={onEdit}
          onRegenerate={onRegenerate}
        />
      ))}
      
      {isLoading && (
        <div className="chat-message-wrapper chat-message-wrapper--assistant">
          <div className="chat-message">
            <div className="chat-message__avatar">
              <Bot />
            </div>
            <div className="chat-message__body">
              <div className="chat-message__bubble">
                <div className="loading-dots">
                  <div className="loading-dots__dot"></div>
                  <div className="loading-dots__dot"></div>
                  <div className="loading-dots__dot"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatArea;
