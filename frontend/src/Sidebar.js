import React from "react";
import "./styles.css";

export default function Sidebar({ chatList, selectedPsid, setSelectedPsid }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span>จัดการสนทนา</span>
      </div>
      <div className="sidebar-tabs">
        <button className="tab active">ทั้งหมด</button>
      </div>
      <div className="chat-list">
        {chatList.length === 0 && (
          <div style={{ color: "#b3b3b3", padding: "24px", textAlign: "center" }}>
            ยังไม่มีรายการแชท
          </div>
        )}
        {chatList.map((c, idx) => (
          <div
            key={c.id}
            className={`chat-user${selectedPsid === c.id ? " selected" : ""}`}
            onClick={() => setSelectedPsid(c.id)}
          >
            {c.profile_pic ?
              <img src={c.profile_pic} alt="profile" className="avatar-pic" />
              :
              <div className="avatar-circle">{(c.name || c.id)[0]}</div>
            }
            <div>
              <div className="user-name">{c.name || c.id}</div>
              <div className="last-msg">{c.lastMsg}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
