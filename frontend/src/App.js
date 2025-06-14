import React, { useState, useEffect } from "react";
import Sidebar from "./ChatHeader";
import ChatArea from "./ChatArea";
import "./styles.css";

export default function App() {
  const [selectedPsid, setSelectedPsid] = useState(null);
  const [chatList, setChatList] = useState([]);
  const [mode, setMode] = useState("admin");  // โหมดเริ่มต้นเป็นแอดมิน

  useEffect(() => {
    const fetchChats = () => {
      fetch("http://localhost:8000/api/chat-list")
        .then(res => res.json())
        .then(data => setChatList(data));
    };
    fetchChats();
    const timer = setInterval(fetchChats, 2000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="app-root">
      <Sidebar
        chatList={chatList}
        selectedPsid={selectedPsid}
        setSelectedPsid={setSelectedPsid}
      />
      <ChatArea
        psid={selectedPsid}
        chatList={chatList}
        mode={mode}  // ส่งโหมดให้ ChatArea
        setMode={setMode}  // ส่ง setMode ให้ ChatArea
      />
    </div>
  );
}
