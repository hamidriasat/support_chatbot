// ─────────────────────────────────────────────
//  components/ChatPanel.js
//
//  A "smart" component — it orchestrates
//  smaller dumb components and owns layout.
//  It uses the useChat hook for all logic.
// ─────────────────────────────────────────────

import React from "react";
import { useChat } from "../hooks/Usechat";
import { MessageList } from "./Messagelist";
import { ChatInput } from "./Chatinput";
import "./Chatpanel.css";

export function ChatPanel() {
  const { messages, isLoading, error, send, clearChat, newChat, isConnected } = useChat();

  return (
    <div className="chat-panel">
      {/* ── Header ── */}
      <header className="chat-panel__header">
        <button
          className="chat-panel__new-chat"
          onClick={newChat}
          title="Start a new conversation"
        >
          ➕ New Chat
        </button>
        <div className="chat-panel__header-info">
          <div 
            className="chat-panel__status-dot" 
            style={{ background: isConnected ? "#22c55e" : "#ef4444" }}
            title={isConnected ? "Backend connected" : "Backend disconnected"}
          />
          <span className="chat-panel__title">Assistant</span>
        </div>
        <button
          className="chat-panel__clear"
          onClick={clearChat}
          title="Clear conversation"
        >
          Clear
        </button>
      </header>

      {/* ── Messages ── */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* ── Error banner ── */}
      {error && (
        <div className="chat-panel__error">
          ⚠ {error}
        </div>
      )}

      {/* ── Input ── */}
      <ChatInput onSend={send} isLoading={isLoading} />
    </div>
  );
}