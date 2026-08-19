import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Zap, Square } from 'lucide-react';

function ChatInput({ onSend, isLoading, disabled, onStop }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) {
      onStop();
      return;
    }
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 150) + 'px';
  };

  return (
    <div className="chat-input">
      <div className="chat-input__shortcuts" style={{ display: 'flex', gap: '12px', marginBottom: '8px', color: 'var(--text-muted)', paddingLeft: '12px' }}>
        <button style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
          <Paperclip size={14} /> Attach
        </button>
        <button style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
          <Zap size={14} /> Templates
        </button>
      </div>
      <form className="chat-input__form" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="chat-input__field"
          placeholder="Ask something about your Gmail inbox"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled && !isLoading}
          rows={1}
        />
        {isLoading ? (
          <button
            type="button"
            className="btn chat-input__send chat-input__send--stop"
            onClick={onStop}
            aria-label="Stop generation"
            title="Stop generation"
          >
            <Square fill="currentColor" />
          </button>
        ) : (
          <button
            type="submit"
            className="btn btn--primary chat-input__send"
            disabled={disabled || !value.trim()}
            aria-label="Send message"
          >
            <Send />
          </button>
        )}
      </form>
    </div>
  );
}

export default ChatInput;
