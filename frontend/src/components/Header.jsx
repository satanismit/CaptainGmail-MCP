import { Mail, Eraser, Trash2, LayoutDashboard, MessageSquare } from 'lucide-react';

function Header({ gmailConnected, groqConfigured, onClearChat, onDisconnect, onToggleSidebar, activeView, onViewChange }) {
  return (
    <header className="header">
      <div className="header__left">
        <button
          className="header__menu-toggle"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar"
        >
          <Mail />
        </button>
        <div className="header__logo">
          <Mail />
        </div>
        <h1 className="header__title">CAPTAINGMAIL-MCP</h1>
        <div className="header__nav">
          <button
            className={`header__nav-btn${activeView === 'chat' ? ' header__nav-btn--active' : ''}`}
            onClick={() => onViewChange('chat')}
          >
            <MessageSquare size={16} />
            Chat
          </button>
          <button
            className={`header__nav-btn${activeView === 'dashboard' ? ' header__nav-btn--active' : ''}`}
            onClick={() => onViewChange('dashboard')}
          >
            <LayoutDashboard size={16} />
            Dashboard
          </button>
        </div>
      </div>
      <div className="header__right">
        {gmailConnected && (
          <div className="header__status">
            <span className="header__status-dot" />
            Connected: Gmail
          </div>
        )}
        <button className="btn btn--ghost btn--small" onClick={onClearChat}>
          <Eraser size={14} />
          Clear chat
        </button>
        <button className="btn btn--ghost btn--small btn--hover-danger" onClick={onDisconnect}>
          <Trash2 size={14} />
          Disconnect
        </button>
      </div>
    </header>
  );
}

export default Header;
