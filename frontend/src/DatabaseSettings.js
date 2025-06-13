import React, { useState, useEffect } from "react";

export default function DatabaseSettings() {
  const [dbType, setDbType] = useState("MongoDB");
  const [databases, setDatabases] = useState([]); // ใช้ useState สำหรับเก็บรายชื่อฐานข้อมูล
  const [collections, setCollections] = useState([]);
  const [selectedDb, setSelectedDb] = useState("");
  const [selectedCollection, setSelectedCollection] = useState("");
  const [newDbName, setNewDbName] = useState("");
  const [newCollectionName, setNewCollectionName] = useState("");
  const [MONGO_URI, setMONGO_URI] = useState("mongodb://localhost:27017");
  const [loading, setLoading] = useState(false);

  // ดึงรายการฐานข้อมูลจาก MongoDB เมื่อเชื่อมต่อ
  useEffect(() => {
    if (MONGO_URI) {
      setLoading(true);
      fetch("http://localhost:8000/get_databases")
        .then((response) => response.json())
        .then((data) => {
          setDatabases(data.databases || []); // ถ้าไม่มีฐานข้อมูลจะใช้ array ว่าง
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching databases:", err);
          setDatabases([]); // ถ้ามีข้อผิดพลาดจะทำให้ databases เป็น array ว่าง
          setLoading(false);
        });
    }
  }, [MONGO_URI]);

  // ดึงรายการคอลเล็กชันจากฐานข้อมูลที่เลือก
  useEffect(() => {
    if (selectedDb) {
      fetch(`http://localhost:8000/get_collections/${selectedDb}`)
        .then((response) => response.json())
        .then((data) => setCollections(data.collections))
        .catch((err) => console.error("Error fetching collections:", err));
    }
  }, [selectedDb]);

  // ฟังก์ชันสำหรับการสร้างฐานข้อมูลใหม่
  const handleCreateDb = () => {
    const data = {
      db_name: newDbName,
      collection_name: newCollectionName,
    };

    fetch("http://localhost:8000/create_db", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((result) => {
        alert(result.message);
        // รีเฟรชฐานข้อมูลหลังจากสร้างใหม่
        fetch("http://localhost:8000/get_databases")
          .then((response) => response.json())
          .then((data) => setDatabases(data.databases));
      })
      .catch((err) => console.error("Error creating database:", err));
  };

  return (
    <div>
      <label htmlFor="dbType">เลือกฐานข้อมูล: </label>
      <select
        id="dbType"
        onChange={(e) => setDbType(e.target.value)}
        value={dbType}
        style={{ marginBottom: "10px" }}
      >
        <option value="MongoDB">MongoDB</option>
        <option value="Pinecone">Pinecone</option>
      </select>

      {dbType === "MongoDB" && (
        <div>
          <input
            type="text"
            placeholder="Enter MongoDB URI"
            value={MONGO_URI}
            onChange={(e) => setMONGO_URI(e.target.value)}
          />
          {loading ? (
            <p>กำลังโหลดฐานข้อมูล...</p>
          ) : (
            <>
              {databases.length > 0 ? (
                <>
                  <label>เลือกฐานข้อมูลที่มีอยู่: </label>
                  <select
                    value={selectedDb}
                    onChange={(e) => setSelectedDb(e.target.value)}
                  >
                    <option value="">Select Database</option>
                    {databases.map((db, idx) => (
                      <option key={idx} value={db}>
                        {db}
                      </option>
                    ))}
                  </select>
                </>
              ) : (
                <p>ไม่พบฐานข้อมูล กรุณาตรวจสอบการเชื่อมต่อ</p>
              )}
            </>
          )}

          {selectedDb && (
            <>
              <label>เลือกคอลเล็กชัน: </label>
              <select
                value={selectedCollection}
                onChange={(e) => setSelectedCollection(e.target.value)}
              >
                <option value="">Select Collection</option>
                {collections.map((col, idx) => (
                  <option key={idx} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <button onClick={handleQueryData}>Query Data</button>
              {queryResult && (
                <div>
                  <h4>Query Result:</h4>
                  <pre>{JSON.stringify(queryResult, null, 2)}</pre>
                </div>
              )}
            </>
          )}

          {!selectedDb && (
            <>
              <input
                type="text"
                placeholder="Enter new MongoDB Database Name"
                value={newDbName}
                onChange={(e) => setNewDbName(e.target.value)}
              />
              <input
                type="text"
                placeholder="Enter new MongoDB Collection Name"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
              />
              <button onClick={handleCreateDb}>สร้างฐานข้อมูลและคอลเล็กชันใหม่</button>
            </>
          )}
        </div>
      )}

      {dbType === "Pinecone" && (
        <div>
          <label>Pinecone API Key:</label>
          <input
            type="password"
            placeholder="Enter Pinecone API Key"
            value={PINECONE_API_KEY}
            onChange={(e) => setPINECONE_API_KEY(e.target.value)}
          />
          <label>Pinecone Environment:</label>
          <input
            type="text"
            placeholder="Enter Pinecone Environment"
            value={PINECONE_ENV}
            onChange={(e) => setPINECONE_ENV(e.target.value)}
          />
        </div>
      )}
    </div>
  );
}
