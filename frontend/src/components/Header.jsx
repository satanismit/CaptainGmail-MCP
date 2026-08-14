function Header({ gmailConnected, groqConfigured, onClearChat, onDisconnect }) {
  return (
    <header className="header">
      <div className="header__left">
        <span className="header__logo">📧</span>
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
          Clear chat
        </button>
        <button className="btn btn--ghost btn--small" onClick={onDisconnect}>
          Disconnect
        </button>
      </div>
    </header>
  );
}

export default Header;
