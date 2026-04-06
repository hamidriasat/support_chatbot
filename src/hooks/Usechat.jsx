// ─────────────────────────────────────────────
//  hooks/useChat.js
//
//  A "custom hook" bundles related state + logic
//  together so your components stay clean.
//
//  Rule of thumb: if it's not about rendering,
//  it belongs in a hook or service.
// ─────────────────────────────────────────────

import { useState, useCallback, useEffect } from "react";
import { sendMessage, checkBackendConnection } from "../services/Api";

// Each message has this shape:
// { id: number, role: "user" | "assistant", text: string }

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Check backend connection on mount and every 5 seconds
  useEffect(() => {
    const checkConnection = async () => {
      const connected = await checkBackendConnection();
      setIsConnected(connected);
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  // useCallback prevents this function from being recreated
  // on every render — good habit for functions passed to components.
  const send = useCallback(async (text) => {
    if (!text.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: "user",
      text: text.trim(),
    };

    // Add user message immediately (optimistic update)
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const reply = await sendMessage(text.trim(), messages);

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: reply,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      // Always runs — clears loading whether success or failure
      setIsLoading(false);
    }
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isLoading, error, send, clearChat, isConnected };
}