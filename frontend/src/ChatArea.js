import React, { useState, useEffect, useRef } from "react";
import MessageInput from "./MessageInput";

import "./styles.css";

// ปุ่มฟันเฟืองสัญลักษณ์เปิดหน้าต่างการตั้งค่า
export default function ChatArea({ psid, chatList, mode }) {
  const [messages, setMessages] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const msgEndRef = useRef(null);

  const currentChat = chatList.find((c) => c.id === psid);

  // เปิด/ปิดการตั้งค่า
  const toggleSettings = () => setShowSettings(!showSettings);

  useEffect(() => {
    if (!psid) return setMessages([]);
    fetch(`http://localhost:8000/api/messages/${psid}`)
      .then(res => res.json())
      .then(setMessages);
  }, [psid, chatList]);

  useEffect(() => {
    if (msgEndRef.current) msgEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-area">
      <div className="chat-header" style={{ display: "flex", alignItems: "center", gap: 16 }}>
        {currentChat?.profile_pic &&
          <img src={currentChat.profile_pic} alt="profile" style={{ width: 38, height: 38, borderRadius: "50%", marginRight: 8 }} />}
        <div>
          <b>{currentChat?.name || psid}</b>
        </div>
        <div style={{ flex: 1 }} />
        {/* ปุ่มฟันเฟืองสำหรับการตั้งค่า */}
        <button onClick={toggleSettings}>⚙️</button>
        <span style={{ fontSize: 14 }}>{mode === "ai" ? "AI Assistant" : "แอดมิน"}</span>
      </div>

      {/* ถ้าเปิดการตั้งค่า */}
      {showSettings && (
        <div className="settings">
          <h3>เลือกฐานข้อมูล</h3>
          <DatabaseSettings />
        </div>
      )}

      <div className="chat-messages">
        {messages.map((m, idx) => (
          <div key={idx} className={`msg-bubble ${m.from === "user" ? "user" : (m.from === "ai" ? "AI" : "ADMIN")}`}>
            {m.text}
          </div>
        ))}
        <div ref={msgEndRef} />
      </div>
      <MessageInput psid={psid} setMessages={setMessages} mode={mode} />
    </div>
  );
}
