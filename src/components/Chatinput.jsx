// ─────────────────────────────────────────────
//  components/ChatInput.js
//
//  "Controlled component" pattern:
//  React owns the input value via state.
//  The DOM never has stale data.
// ─────────────────────────────────────────────

import React, { useState } from "react";
import "./Chatinput.css";

export function ChatInput({ onSend, isLoading }) {
  // useState returns [currentValue, setterFunction]
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    if (!value.trim() || isLoading) return;
    onSend(value);      // lift data UP to the parent
    setValue("");        // clear the input
  };

  // Allow Shift+Enter for new lines, Enter alone to send
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // stop the default newline
      handleSubmit();
    }
  };

  return (
    <div className="chat-input">
      <textarea
        className="chat-input__textarea"
        rows={1}
        placeholder="Type a message…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
      />
      <button
        className="chat-input__send"
        onClick={handleSubmit}
        disabled={!value.trim() || isLoading}
        aria-label="Send message"
      >
        {/* Simple SVG arrow icon — no dependency needed */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.2"
          strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  );
}