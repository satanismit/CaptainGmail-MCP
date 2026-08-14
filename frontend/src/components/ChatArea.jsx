import { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

function ChatArea({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="chat-area">
        <div className="chat-area__empty">
          <div className="chat-area__empty-icon">💬</div>
          <p className="chat-area__empty-text">
            Ask something about your Gmail inbox
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-area">
      {messages.map((msg, index) => (
        <ChatMessage key={index} message={msg} />
      ))}
      {isLoading && (
        <div className="chat-message chat-message--assistant">
          <div className="chat-message__avatar">🤖</div>
          <div className="chat-message__body">
            <div className="loading-dots">
              <div className="loading-dots__dot" />
              <div className="loading-dots__dot" />
              <div className="loading-dots__dot" />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

export default ChatArea;
