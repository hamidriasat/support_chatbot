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
import { sendMessage, checkBackendConnection, sendApproval } from "../services/Api";
import { generateUUID } from "../utils/uuid";

// Each message has this shape:
// { id: number, role: "user" | "assistant", text: string }

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [waitingForApproval, setWaitingForApproval] = useState(false);

  // Check backend connection on mount and every 5 seconds
  // Also generate UUID for this chat session on mount
  useEffect(() => {
    const checkConnection = async () => {
      const connected = await checkBackendConnection();
      setIsConnected(connected);
    };

    // Generate UUID for new chat on first load
    setChatId(generateUUID());

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  // useCallback prevents this function from being recreated
  // on every render — good habit for functions passed to components.
  const send = useCallback(async (text) => {
    if (!text.trim() || !chatId) return;

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
      const reply = await sendMessage(text.trim(), messages, chatId);

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: reply.response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setWaitingForApproval(reply.waiting_for_approval);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      // Always runs — clears loading whether success or failure
      setIsLoading(false);
    }
  }, [messages, chatId]);

  const handleApproval = useCallback(async (approved) => {
    try {
      setIsLoading(true);
      
      // Add approval message to chat
      const approvalText = approved ? "yes" : "no";
      const approvalMessage = {
        id: Date.now(),
        role: "user",
        text: approvalText,
      };
      
      setMessages((prev) => [...prev, approvalMessage]);
      const reply = await sendApproval(approved, chatId);
      
      // Add assistant response to chat
      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: reply.response,
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      setWaitingForApproval(reply.waiting_for_approval);
    } catch (err) {
      setError(err.message || "Failed to send approval. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setWaitingForApproval(false);
  }, []);

  const newChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setWaitingForApproval(false);
    setChatId(generateUUID());
  }, []);

  return { messages, isLoading, error, send, clearChat, newChat, isConnected, chatId, waitingForApproval, handleApproval };
}