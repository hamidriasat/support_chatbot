// ─────────────────────────────────────────────
//  services/api.js
//  All communication with your FastAPI backend
//  lives in ONE place. If the URL changes, you
//  only update BASE_URL — nothing else.
// ─────────────────────────────────────────────

// Use relative URLs to leverage Vite proxy in development
// For production, set VITE_API_URL environment variable
const BASE_URL = import.meta.env.VITE_API_URL || "";

/**
 * Send a message to the FastAPI backend.
 *
 * @param {string} message   - The user's text
 * @param {Array}  history   - Previous messages (optional, for context)
 * @param {string} chatId    - UUID for this chat session
 * @returns {Promise<{response: string, waiting_for_approval: boolean}>} - The assistant's reply and approval status
 */
export async function sendMessage(message, history = [], chatId) {
  try {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, history, chat_id: chatId }),
    });

    if (!response.ok) {
      // Throw a real Error so we can catch it in the UI
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // ── Return both response and approval status ──
    return {
      response: data.response ?? "No response from server.",
      waiting_for_approval: data.waiting_for_approval ?? false,
    };
  } catch (err) {
    console.error("Error sending message:", err);
    throw err;
  }
}

/**
 * Send approval decision to the backend as a message.
 *
 * @param {boolean} approved - True if user approved, false if rejected
 * @param {string} chatId    - UUID for this chat session
 * @returns {Promise<{response: string, waiting_for_approval: boolean}>} - The backend response
 */
export async function sendApproval(approved, chatId) {
  try {
    const approvalMessage = approved ? "yes" : "no";
    
    const response = await fetch(`${BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: approvalMessage, chat_id: chatId }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      response: data.response ?? "No response from server.",
      waiting_for_approval: data.waiting_for_approval ?? false,
    };
  } catch (err) {
    console.error("Error sending approval:", err);
    throw err;
  }
}

/**
 * Check if the backend is connected and healthy.
 *
 * @returns {Promise<boolean>} - True if backend is reachable, false otherwise
 */
export async function checkBackendConnection() {
  try {
    const response = await fetch(`${BASE_URL}/health`, {
      method: "GET",
    });
    console.log("Health check response:", response.status);
    return response.ok;
  } catch (err) {
    // Backend is unreachable or timed out
    console.error("Health check failed:", err);
    return false;
  }
}