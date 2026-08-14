import { useState, useRef } from 'react';

function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
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
      <form className="chat-input__form" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="chat-input__field"
          placeholder="Ask something about your Gmail inbox"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />
        <button
          type="submit"
          className="btn btn--primary chat-input__send"
          disabled={disabled || !value.trim()}
        >
          ↑
        </button>
      </form>
    </div>
  );
}

export default ChatInput;
