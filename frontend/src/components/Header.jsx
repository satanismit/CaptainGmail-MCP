import { Mail, Eraser, Trash2 } from 'lucide-react';

function Header({ gmailConnected, groqConfigured, onClearChat, onDisconnect, onToggleSidebar }) {
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
