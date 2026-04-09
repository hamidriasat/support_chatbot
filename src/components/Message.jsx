// ─────────────────────────────────────────────
//  components/Message.js
//
//  A "dumb" component — it only receives props
//  and renders them. No state, no logic.
//  These are the easiest components to test.
// ─────────────────────────────────────────────
import "./Message.css";

// props are values passed in from the parent
// { role: "user" | "assistant", text: string }
export function Message({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`message message--${role}`}>
      <div className="message__avatar">
        {isUser ? "You" : "AI"}
      </div>
      <div className="message__bubble">
        <p className="message__text">{text}</p>
      </div>
    </div>
  );
}