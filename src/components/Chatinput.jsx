// ─────────────────────────────────────────────
//  components/ChatInput.js
//
//  "Controlled component" pattern:
//  React owns the input value via state.
//  The DOM never has stale data.
// ─────────────────────────────────────────────

import React, { useState, useEffect } from "react";
import "./Chatinput.css";

export function ChatInput({ onSend, isLoading, waitingForApproval, onApproval, isRecording, onStartRecording, onStopRecording, approvalType }) {
  // useState returns [currentValue, setterFunction]
  const [value, setValue] = useState("");
  const [recordingTime, setRecordingTime] = useState(0);

  // Update recording time every second
  useEffect(() => {
    if (!isRecording) {
      setRecordingTime(0);
      return;
    }

    const interval = setInterval(() => {
      setRecordingTime((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRecording]);

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

  const formatRecordingTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="chat-input">
      {/* Text approval buttons - only show for text mode */}
      {waitingForApproval && approvalType === "text" && (
        <div className="chat-input__approval">
          <span className="chat-input__approval-text">Confirm the changes</span>
          <div className="chat-input__approval-buttons">
            <button
              className="chat-input__approval-yes"
              onClick={() => onApproval(true)}
              disabled={isLoading}
              title="Confirm and proceed"
            >
              Yes
            </button>
            <button
              className="chat-input__approval-no"
              onClick={() => onApproval(false)}
              disabled={isLoading}
              title="Reject changes"
            >
              No
            </button>
          </div>
        </div>
      )}

      {/* Voice approval pending - show message instead of buttons */}
      {waitingForApproval && approvalType === "voice" && (
        <div className="chat-input__approval chat-input__approval--voice">
          <span className="chat-input__approval-text">🎤 Approval pending - Please record your response</span>
        </div>
      )}
      
      {/* Recording status */}
      {isRecording && (
        <div className="chat-input__recording-status">
          <div className="chat-input__recording-indicator" />
          <span className="chat-input__recording-text">Recording... {formatRecordingTime(recordingTime)}</span>
        </div>
      )}

      <div className="chat-input__input-container">
        <textarea
          className="chat-input__textarea"
          rows={1}
          placeholder="Type a message…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || isRecording || (waitingForApproval && approvalType === "voice")}
        />
        
        {/* Microphone button */}
        <button
          className={`chat-input__mic ${isRecording ? "chat-input__mic--recording" : ""}`}
          onMouseDown={onStartRecording}
          onMouseUp={onStopRecording}
          onTouchStart={onStartRecording}
          onTouchEnd={onStopRecording}
          disabled={isLoading}
          aria-label={isRecording ? "Stop recording" : "Start recording"}
          title={isRecording ? "Release to stop recording" : "Hold to record"}
        >
          {/* Microphone icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.2"
            strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v12a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </button>

        {/* Send button */}
        <button
          className="chat-input__send"
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading || isRecording}
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
    </div>
  );
}