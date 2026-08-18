import { useState, useEffect, useCallback } from 'react';
import { getStatus, connectGmail, disconnectGmail } from './services/api';
import { useChat } from './hooks/useChat';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import DraftPreview from './components/DraftPreview';
import './App.css';

function App() {
  const [gmailConnected, setGmailConnected] = useState(false);
  const [aiConfigured, setAiConfigured] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const {
    messages,
    isLoading,
    pendingAction,
    sendMessage,
    clearChat,
    dismissPendingAction,
    confirmDraftCreated,
  } = useChat();

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getStatus();
      setGmailConnected(data.gmail_connected);
      setAiConfigured(data.ai_configured);
    } catch {
      // Backend may not be running yet
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      await connectGmail();
      setGmailConnected(true);
      showToast('Gmail connected successfully.');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectGmail();
      setGmailConnected(false);
      clearChat();
      showToast('Gmail disconnected.');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleTemplateUse = (templateText) => {
    sendMessage(templateText);
  };

  if (statusLoading) {
    return (
      <div className="app-layout app-layout--disconnected">
        <div className="connect-screen">
          <div className="connect-screen__icon">📧</div>
          <div className="connect-screen__title">Loading...</div>
        </div>
      </div>
    );
  }

  if (!gmailConnected) {
    return (
      <div className="app-layout app-layout--disconnected">
        <div className="connect-screen">
          <div className="connect-screen__icon">📧</div>
          <h1 className="connect-screen__title">CAPTAINGMAIL-MCP</h1>
          <p className="connect-screen__subtitle">
            Connect your Gmail account to search, summarize, and draft emails
            with AI.
          </p>
          {!aiConfigured && (
            <div className="connect-screen__warning">
              ⚠️ Set API_KEY and MODEL in your .env file to enable
              chat.
            </div>
          )}
          <button
            className="btn btn--primary"
            onClick={handleConnect}
            disabled={isConnecting}
          >
            {isConnecting ? 'Connecting...' : '🔗 Connect Gmail'}
          </button>
        </div>
        {toast && (
          <div className="toast-container">
            <div className={`toast toast--${toast.type}`}>{toast.message}</div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar onUseTemplate={handleTemplateUse} />
      <div className="main-content">
        <Header
          gmailConnected={gmailConnected}
          groqConfigured={aiConfigured}
          onClearChat={clearChat}
          onDisconnect={handleDisconnect}
        />
        {!aiConfigured && (
          <div
            style={{
              padding: '12px 24px',
              background: 'var(--warning-light)',
              borderBottom: '1px solid rgba(245, 158, 11, 0.2)',
              color: 'var(--warning)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            ⚠️ Set API_KEY and MODEL in your .env file to enable
            chat.
          </div>
        )}
        <ChatArea messages={messages} isLoading={isLoading} />
        {pendingAction && (
          <DraftPreview
            pendingAction={pendingAction}
            onConfirm={confirmDraftCreated}
            onCancel={dismissPendingAction}
            showToast={showToast}
          />
        )}
        <ChatInput
          onSend={sendMessage}
          disabled={isLoading || !aiConfigured}
        />
      </div>
      {toast && (
        <div className="toast-container">
          <div className={`toast toast--${toast.type}`}>{toast.message}</div>
        </div>
      )}
    </div>
  );
}

export default App;
