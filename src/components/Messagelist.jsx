// ─────────────────────────────────────────────
//  components/MessageList.js
//
//  Renders all messages and auto-scrolls to
//  the bottom when new ones arrive.
//
//  useRef  — points to a real DOM element
//  useEffect — runs side-effects after render
// ─────────────────────────────────────────────

import React, { useRef, useEffect } from "react";
import { Message } from "./Message";
import "./Messagelist.css";

export function MessageList({ messages, isLoading }) {
  // useRef gives us a direct handle on the DOM node
  const bottomRef = useRef(null);

  // useEffect runs AFTER the component renders.
  // The dependency array [messages, isLoading] means:
  // "re-run this effect whenever messages or isLoading changes."
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="message-list message-list--empty">
        <div className="message-list__empty-state">
          <span className="message-list__empty-icon">💬</span>
          <p>Start a conversation</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg) => (
        // key= tells React how to track list items efficiently
        <Message key={msg.id} role={msg.role} text={msg.text} />
      ))}

      {/* Typing indicator shown while waiting for API */}
      {isLoading && (
        <div className="message message--assistant">
          <div className="message__avatar" style={{
            width: 34, height: 34, borderRadius: "50%",
            background: "var(--color-accent)", color: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 11, fontWeight: 700, flexShrink: 0
          }}>AI</div>
          <div className="typing-indicator">
            <span /><span /><span />
          </div>
        </div>
      )}

      {/* Invisible div at the bottom — we scroll to this */}
      <div ref={bottomRef} />
    </div>
  );
}