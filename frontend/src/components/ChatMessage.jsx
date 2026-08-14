import ToolActivity from './ToolActivity';

function ChatMessage({ message }) {
  const { role, content, isError, toolHistory } = message;
  const isUser = role === 'user';

  let className = 'chat-message';
  if (isUser) className += ' chat-message--user';
  else className += ' chat-message--assistant';
  if (isError) className += ' chat-message--error';

  return (
    <div className={className}>
      <div className="chat-message__avatar">{isUser ? '👤' : '🤖'}</div>
      <div className="chat-message__body">
        <div className="chat-message__bubble">{content}</div>
        {toolHistory && toolHistory.length > 0 && (
          <ToolActivity toolHistory={toolHistory} />
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
