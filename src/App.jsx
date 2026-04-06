import React from "react";
import { ChatPanel } from "./components/Chatpanel";
import "./styles/Globals.css";
import "./App.css";

function App() {
  return (
    <div className="app-layout">
      {/* Chat area — 70% */}
      <main className="app-layout__chat">
        <ChatPanel />
      </main>

      {/* Side panel — 30%, reserved for future use */}
      <aside className="app-layout__side" />
    </div>
  );
}

export default App;