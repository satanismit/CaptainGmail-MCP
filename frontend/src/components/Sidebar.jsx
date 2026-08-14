import { useState } from 'react';
import TEMPLATES from '../data/templates';

function Sidebar({ onUseTemplate }) {
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
    }
  };

  const handleCopy = () => {
    if (selectedText.trim()) {
      navigator.clipboard.writeText(selectedText).catch(() => {});
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <h2 className="sidebar__title">Prompt Templates</h2>
      </div>
      <div className="sidebar__templates">
        {templateEntries.map(([name, text]) => {
          const isOpen = expandedTemplate === name;
          return (
            <div className="template-item" key={name}>
              <button
                className={`template-item__header${
                  isOpen ? ' template-item__header--active' : ''
                }`}
                onClick={() => handleToggle(name)}
              >
                <span
                  className={`template-item__arrow${
                    isOpen ? ' template-item__arrow--open' : ''
                  }`}
                >
                  ▶
                </span>
                {name}
              </button>
              <div
                className={`template-item__content${
                  isOpen ? ' template-item__content--open' : ''
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
            Selected template (edit &amp; copy into chat)
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
