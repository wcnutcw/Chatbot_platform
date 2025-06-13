// frontend/src/MessageInput.js
import React, { useState } from "react";

export default function MessageInput({ psid, setMessages, mode = "admin" }) {
  const [value, setValue] = useState("");

  const send = () => {
    if (!value.trim()) return;
    if (mode === "ai") {
      fetch("http://localhost:8000/api/ai-assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ psid, text: value })
      })
        .then(res => res.json())
        .then(data => {
          setMessages(msgs => [
            ...msgs,
            { from: "user", text: value },
            { from: "ai", text: data.reply }
          ]);
          setValue("");
        });
    } else {
      fetch("http://localhost:8000/api/send-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ psid, text: value })
      })
        .then(res => res.json())
        .then(() => {
          setMessages(msgs => [...msgs, { from: "admin", text: value }]);
          setValue("");
        });
    }
  };

  return (
    <div className="msg-input-bar">
      <input
        type="text"
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => e.key === "Enter" && send()}
        placeholder="Enter ข้อความ... / Shift+Enter ขึ้นบรรทัดใหม่"
      />
      <button onClick={send}>ส่ง</button>
    </div>
  );
}
