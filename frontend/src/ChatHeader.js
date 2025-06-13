import React from "react";
import "./styles.css";

export default function ChatHeader({ chat, mode, setMode }) {
  return (
    <div className="chat-header">
      <div>
        <b>{chat.name}</b>
      </div>
      <div className="toggle-wrap">
        <span>AI Assistant</span>
        <label className="switch">
          <input 
            type="checkbox" 
            checked={mode === "ADMIN"} 
            onChange={() => setMode(mode === "AI" ? "ADMIN" : "AI")}
          />
          <span className="slider"></span>
        </label>
        <span>แอดมิน</span>
      </div>
    </div>
  );
}
