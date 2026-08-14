import { useState, useCallback } from 'react';
import { sendChatMessage } from '../services/api';

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(
    async (messageText) => {
      const trimmed = messageText.trim();
      if (!trimmed) return;

      setError(null);

      // Build conversation history from existing messages (before adding the new one)
      const conversationHistory = messages
        .filter((m) => (m.role === 'user' || m.role === 'assistant') && m.content)
        .map(({ role, content }) => ({ role, content }));

      const userMessage = { role: 'user', content: trimmed };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const result = await sendChatMessage(trimmed, conversationHistory);

        if (result.pending_action) {
          setPendingAction(result.pending_action);
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: 'I prepared a Gmail draft. Review it below before creating it.',
              toolHistory: result.tool_history,
            },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: result.answer,
              toolHistory: result.tool_history,
            },
          ]);
        }
      } catch (err) {
        setError(err.message);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: err.message,
            isError: true,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages],
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setPendingAction(null);
    setError(null);
  }, []);

  const dismissPendingAction = useCallback(() => {
    setPendingAction(null);
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: 'Draft creation cancelled. No Gmail draft was created.',
      },
    ]);
  }, []);

  const confirmDraftCreated = useCallback(() => {
    setPendingAction(null);
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
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
  };
}
