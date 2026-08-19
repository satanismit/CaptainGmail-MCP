import { useState, useCallback, useRef } from 'react';
import { sendChatMessage } from '../services/api';

function generateId() {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 9);
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [error, setError] = useState(null);
  
  const abortControllerRef = useRef(null);

  const performSend = async (messageText, historyUpToNow) => {
    setError(null);
    setIsLoading(true);

    const userMsgId = generateId();
    const userMessage = { id: userMsgId, role: 'user', content: messageText };
    setMessages((prev) => [...prev, userMessage]);

    // Create a new AbortController for this request
    abortControllerRef.current = new AbortController();

    try {
      const result = await sendChatMessage(messageText, historyUpToNow, abortControllerRef.current.signal);

      if (result.pending_action) {
        setPendingAction(result.pending_action);
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'assistant',
            content: 'I prepared a Gmail draft. Review it below before creating it.',
            toolHistory: result.tool_history,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'assistant',
            content: result.answer,
            toolHistory: result.tool_history,
          },
        ]);
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        // Handle aborted fetch gracefully
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'system',
            content: 'Response stopped',
          }
        ]);
      } else {
        setError(err.message);
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: 'assistant',
            content: err.message,
            isError: true,
          },
        ]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const sendMessage = useCallback(
    (messageText) => {
      const trimmed = messageText.trim();
      if (!trimmed) return;

      const conversationHistory = messages
        .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
        .map(({ role, content }) => ({ role, content }));

      performSend(trimmed, conversationHistory);
    },
    [messages]
  );

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const deleteMessage = useCallback((id) => {
    setMessages((prev) => {
      const index = prev.findIndex(m => m.id === id);
      if (index === -1) return prev;
      
      const msgToDelete = prev[index];
      const newMessages = [...prev];
      
      // If it's a user message, check if the immediately following message is an assistant response
      // and delete that paired response too.
      let deleteCount = 1;
      if (msgToDelete.role === 'user' && index + 1 < prev.length) {
        const nextMsg = prev[index + 1];
        // We consider the next message paired if it's not another user message
        if (nextMsg.role === 'assistant' || nextMsg.role === 'system' || nextMsg.isError) {
          deleteCount = 2;
        }
      }
      
      newMessages.splice(index, deleteCount);
      return newMessages;
    });
  }, []);

  const editMessage = useCallback((id, newText) => {
    const trimmed = newText.trim();
    if (!trimmed) return;

    // Find the message
    const index = messages.findIndex(m => m.id === id);
    if (index === -1) return;

    // Build history up to this message
    const historyUpToNow = messages
      .slice(0, index)
      .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
      .map(({ role, content }) => ({ role, content }));

    // Truncate the chat to just before the edited message
    setMessages(prev => prev.slice(0, index));
    
    // Resend it
    performSend(trimmed, historyUpToNow);
  }, [messages]);

  const regenerateResponse = useCallback((id) => {
    const index = messages.findIndex(m => m.id === id);
    if (index === -1) return;

    const assistantMsg = messages[index];
    if (assistantMsg.role !== 'assistant' && assistantMsg.role !== 'system') return;

    // Find the closest preceding user message
    let userMsgIndex = -1;
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMsgIndex = i;
        break;
      }
    }

    if (userMsgIndex === -1) return; // Cannot regenerate if no user prompt

    const userMsgText = messages[userMsgIndex].content;

    // Build history up to that user message
    const historyUpToNow = messages
      .slice(0, userMsgIndex)
      .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
      .map(({ role, content }) => ({ role, content }));

    // Truncate chat to remove the assistant response and the user message (performSend adds it back)
    setMessages(prev => prev.slice(0, userMsgIndex));
    
    // Resend
    performSend(userMsgText, historyUpToNow);
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setPendingAction(null);
    setError(null);
    stopGeneration();
  }, [stopGeneration]);

  const dismissPendingAction = useCallback(() => {
    setPendingAction(null);
    setMessages((prev) => [
      ...prev,
      {
        id: generateId(),
        role: 'system',
        content: 'Draft creation cancelled. No Gmail draft was created.',
      },
    ]);
  }, []);

  const confirmDraftCreated = useCallback(() => {
    setPendingAction(null);
    setMessages((prev) => [
      ...prev,
      {
        id: generateId(),
        role: 'system',
        content: 'Draft created successfully in Gmail. It has not been sent.',
      },
    ]);
  }, []);

  return {
    messages,
    isLoading,
    pendingAction,
    error,
    sendMessage,
    clearChat,
    dismissPendingAction,
    confirmDraftCreated,
    deleteMessage,
    editMessage,
    regenerateResponse,
    stopGeneration
  };
}
