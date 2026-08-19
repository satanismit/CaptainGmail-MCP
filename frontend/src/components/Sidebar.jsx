import { useState } from 'react';
import { ChevronRight, Mail, Reply, Clock, FileText, Calendar, MessageSquare, Code } from 'lucide-react';
import TEMPLATES from '../data/templates';

function getIconForTemplate(name) {
  switch (name) {
    case 'Professional new message':
      return <Mail size={16} color="var(--google-blue)" />;
    case 'Reply to message (by ID)':
      return <Reply size={16} color="var(--google-green)" />;
    case 'Follow-up':
      return <Clock size={16} color="var(--google-yellow)" />;
    case 'Summarize thread into reply':
      return <FileText size={16} color="var(--google-blue)" />;
    case 'Meeting / schedule request':
      return <Calendar size={16} color="var(--google-green)" />;
    case 'Casual short':
      return <MessageSquare size={16} color="var(--google-blue)" />;
    case 'Return JSON draft (tool)':
      return <Code size={16} color="var(--google-red)" />;
    default:
      return <Mail size={16} color="var(--text-secondary)" />;
  }
}

function Sidebar({ onUseTemplate, isOpen, onClose }) {
  const [expandedTemplate, setExpandedTemplate] = useState(null);
  const [selectedText, setSelectedText] = useState('');

  const templateEntries = Object.entries(TEMPLATES);

  const handleToggle = (name) => {
    setExpandedTemplate((prev) => (prev === name ? null : name));
  };

  const handleSelect = (text) => {
    setSelectedText(text);
  };

  const handleUse = () => {
    if (selectedText.trim()) {
      onUseTemplate(selectedText);
      if (onClose) onClose();
    }
  };

  const handleCopy = () => {
    if (selectedText.trim()) {
      navigator.clipboard.writeText(selectedText).catch(() => {});
    }
  };

  return (
    <aside className={`sidebar${isOpen ? ' sidebar--open' : ''}`}>
      <div className="sidebar__header">
        <h2 className="sidebar__title">Prompt Templates</h2>
      </div>
      <div className="sidebar__templates">
        {templateEntries.map(([name, text]) => {
          const isExpanded = expandedTemplate === name;
          return (
            <div className="template-item" key={name}>
              <button
                className={`template-item__header${
                  isExpanded ? ' template-item__header--active' : ''
                }`}
                onClick={() => handleToggle(name)}
              >
                <span className="template-item__icon">
                  {getIconForTemplate(name)}
                </span>
                {name}
                <span
                  className={`template-item__arrow${
                    isExpanded ? ' template-item__arrow--open' : ''
                  }`}
                >
                  <ChevronRight />
                </span>
              </button>
              <div
                className={`template-item__content${
                  isExpanded ? ' template-item__content--open' : ''
                }`}
              >
                <p className="template-item__text">{text}</p>
                <div className="template-item__actions">
                  <button
                    className="btn btn--secondary btn--small"
                    onClick={() => handleSelect(text)}
                  >
                    Select
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      {selectedText && (
        <div className="sidebar__selected">
          <div className="sidebar__selected-label">
            Selected template
          </div>
          <textarea
            className="sidebar__selected-textarea"
            value={selectedText}
            onChange={(e) => setSelectedText(e.target.value)}
          />
          <div className="sidebar__selected-actions">
            <button
              className="btn btn--primary btn--small"
              onClick={handleUse}
            >
              Use in chat
            </button>
            <button
              className="btn btn--secondary btn--small"
              onClick={handleCopy}
            >
              Copy
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
