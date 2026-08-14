import { useState } from 'react';

function ToolActivity({ toolHistory }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!toolHistory || toolHistory.length === 0) return null;

  return (
    <div className="tool-activity">
      <button
        className="tool-activity__toggle"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span
          className={`tool-activity__arrow${
            isOpen ? ' tool-activity__arrow--open' : ''
          }`}
        >
          ▶
        </span>
        Tool activity ({toolHistory.length} call{toolHistory.length !== 1 ? 's' : ''})
      </button>
      <div
        className={`tool-activity__content${
          isOpen ? ' tool-activity__content--open' : ''
        }`}
      >
        {toolHistory.map((call, index) => (
          <div className="tool-activity__call" key={index}>
            <div className="tool-activity__call-name">
              {index + 1}. {call.tool_name}
            </div>
            <pre className="tool-activity__call-args">
              {JSON.stringify(call.arguments, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ToolActivity;
