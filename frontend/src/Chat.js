import React, { useState, useRef } from "react";
import { sendChat, uploadFile, getFiles } from "./api";

export default function Chat({ mode, db }) {
  const [messages, setMessages] = useState([]);
  const [msg, setMsg] = useState("");
  const [fileList, setFileList] = useState([]);
  const fileRef = useRef();

  // ดึงรายชื่อไฟล์เมื่อ db เปลี่ยน
  React.useEffect(() => {
    getFiles(db).then(res => setFileList(res.data.files));
  }, [db, messages]);

  const send = async () => {
    if (!msg) return;
    setMessages(m => [...m, { user: "me", text: msg }]);
    setMsg("");
    const res = await sendChat(msg, mode);
    setMessages(m => [...m, { user: mode, text: res.data.reply }]);
  };

  const handleUpload = async (e) => {
    if (!e.target.files[0]) return;
    await uploadFile(e.target.files[0], db);
    fileRef.current.value = "";
    getFiles(db).then(res => setFileList(res.data.files));
  };

  return (
    <div style={{ padding: 20, height: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, overflowY: "auto", marginBottom: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            textAlign: m.user === "me" ? "right" : "left",
            margin: "6px 0"
          }}>
            <span style={{
              display: "inline-block", padding: "6px 14px", borderRadius: 16,
              background: m.user === "me" ? "#bae6fd" : m.user === "AI" ? "#f0fdfa" : "#fef2f2"
            }}>
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div>
        <input
          value={msg}
          onChange={e => setMsg(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="พิมพ์ข้อความ..."
          style={{ width: "70%", padding: 8 }}
        />
        <button onClick={send} style={{ marginLeft: 6 }}>ส่ง</button>
        <input type="file" ref={fileRef} onChange={handleUpload} style={{ marginLeft: 10 }} />
      </div>
      <div style={{ marginTop: 10 }}>
        <b>ไฟล์ใน {db}:</b>
        <ul>
          {fileList.map((f, idx) => <li key={idx}>{f.filename} ({f.size} bytes)</li>)}
        </ul>
      </div>
    </div>
  );
}
