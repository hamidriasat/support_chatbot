// ─────────────────────────────────────────────
//  hooks/useChat.js
//
//  A "custom hook" bundles related state + logic
//  together so your components stay clean.
//
//  Rule of thumb: if it's not about rendering,
//  it belongs in a hook or service.
// ─────────────────────────────────────────────

import { useState, useCallback, useEffect, useRef } from "react";
import { sendMessage, checkBackendConnection, sendApproval, sendVoice } from "../services/Api";
import { generateUUID } from "../utils/uuid";
import { startRecording, stopRecording, blobToBase64, playAudio } from "../utils/audioRecorder";

// Each message has this shape:
// { id: number, role: "user" | "assistant", text: string }

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [waitingForApproval, setWaitingForApproval] = useState(false);
  const [approvalType, setApprovalType] = useState("text"); // "text" or "voice"
  
  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const autoStopTimerRef = useRef(null);

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
    return () => {
      clearInterval(interval);
      // Cleanup: stop any ongoing recording and clear timer
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (autoStopTimerRef.current) {
        clearTimeout(autoStopTimerRef.current);
      }
    };
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
      
      // Set approval type to text if waiting for approval
      if (reply.waiting_for_approval) {
        setApprovalType("text");
      }
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      // Always runs — clears loading whether success or failure
      setIsLoading(false);
    }
  }, [messages, chatId]);

  const handleApproval = useCallback(async (approved) => {
  // Only handle TEXT approval here
  // Voice approval is handled through voice recording
    if (approvalType === "voice") {
      console.error("Voice approval should be sent via voice recording, not buttons");
      return;
    }

    try {
      setIsLoading(true);
    
      const approvalText = approved ? "yes" : "no";
      const approvalMessage = {
        id: Date.now(),
        role: "user",
        text: approvalText,
      };
    
      setMessages((prev) => [...prev, approvalMessage]);
    
      const reply = await sendApproval(approved, chatId);
    
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
  }, [chatId, approvalType]);

  // Start recording audio
  const startVoiceRecording = useCallback(async () => {
    try {
      setError(null);
      const mediaRecorder = await startRecording();
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);

      // Auto-stop after 30 seconds
      const timer = setTimeout(() => {
        stopVoiceRecording();
      }, 30000);
      autoStopTimerRef.current = timer;
    } catch (err) {
      setError("Failed to access microphone. Please check permissions.");
      console.error("Error starting recording:", err);
    }
  }, []);

  // Stop recording audio and send it
  const stopVoiceRecording = useCallback(async () => {
    if (!mediaRecorderRef.current) return;

    try {
      setIsRecording(false);
      
      // Clear the auto-stop timer if it exists
      if (autoStopTimerRef.current) {
        clearTimeout(autoStopTimerRef.current);
        autoStopTimerRef.current = null;
      }

      const audioBlob = await stopRecording(mediaRecorderRef.current);
      mediaRecorderRef.current = null;

      // Send the voice message
      setIsLoading(true);
      setError(null);

      const reply = await sendVoice(audioBlob, chatId);

      // Add transcription as user message
      if (reply.transcription) {
        const userMessage = {
          id: Date.now(),
          role: "user",
          text: reply.transcription,
        };
        setMessages((prev) => [...prev, userMessage]);
      }

      // Add response as assistant message
      if (reply.response) {
        const assistantMessage = {
          id: Date.now() + 1,
          role: "assistant",
          text: reply.response,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }

      setWaitingForApproval(reply.waiting_for_approval);
      
      // Set approval type to voice if waiting for approval
      if (reply.waiting_for_approval) {
        setApprovalType("voice");
      }

      // Play the audio response if available
      if (reply.audio) {
        playAudio(reply.audio);
      }
    } catch (err) {
      setError(err.message || "Failed to send voice message. Please try again.");
      console.error("Error sending voice message:", err);
    } finally {
      setIsLoading(false);
    }
  }, [chatId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setWaitingForApproval(false);
    setApprovalType("text");
  }, []);

  const newChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setWaitingForApproval(false);
    setApprovalType("text");
    setChatId(generateUUID());
  }, []);

  return { 
    messages, 
    isLoading, 
    error, 
    send, 
    clearChat, 
    newChat, 
    isConnected, 
    chatId, 
    waitingForApproval, 
    handleApproval,
    isRecording,
    startVoiceRecording,
    stopVoiceRecording,
    approvalType,
  };
}