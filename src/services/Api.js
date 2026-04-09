// ─────────────────────────────────────────────
//  services/api.js
//  All communication with your FastAPI backend
//  lives in ONE place. If the URL changes, you
//  only update BASE_URL — nothing else.
// ─────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_URL || "";

/**
 * Send a message to the FastAPI backend.
 *
 * @param {string} message   - The user's text
 * @param {Array}  history   - Previous messages (optional, for context)
 * @param {string} chatId    - UUID for this chat session
 * @returns {Promise<string>} - The assistant's reply
 */
export async function sendMessage(message, history = [], chatId) {
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

  // ── Adjust this key to match your FastAPI response shape ──
  // e.g. if your API returns { reply: "..." } use data.reply
  // e.g. if it returns { message: "..." } use data.message
  return data.response ?? "No response from server.";
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
    return response.ok;
  } catch (err) {
    // Backend is unreachable or timed out
    return false;
  }
}