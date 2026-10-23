import { useRef, useEffect } from 'react';
import { Send, Paperclip, Zap, Square } from 'lucide-react';

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'concise', label: 'Concise' },
  { value: 'formal', label: 'Formal' },
];

function ChatInput({ onSend, isLoading, disabled, onStop, tone, onToneChange, value, onValueChange, focusToken }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (focusToken && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [focusToken]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) {
      onStop();
      return;
    }
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed, tone);
    onValueChange('');
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
    onValueChange(e.target.value);
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
        <button type="button" style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
          <Zap size={14} /> Templates
        </button>
        <label className="tone-selector">
          <span className="tone-selector__label">Tone</span>
          <select value={tone} onChange={(e) => onToneChange(e.target.value)} aria-label="Email writing tone">
            {TONES.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>
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
