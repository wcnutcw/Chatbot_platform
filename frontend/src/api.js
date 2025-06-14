import axios from "axios";
const API = "http://localhost:8000/api";

export const sendChat = (message, mode) =>
  axios.post(`${API}/chat`, 
    { message, mode }, 
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, transformRequest: [(data) => {
        // convert JS obj to x-www-form-urlencoded
        return Object.entries(data).map(([k,v])=>encodeURIComponent(k)+'='+encodeURIComponent(v)).join('&')
    }]}
  );

export const uploadFile = (file, db) => {
  const data = new FormData();
  data.append("file", file);
  data.append("db", db);
  return axios.post(`${API}/upload`, data);
};

export const getFiles = (db) =>
  axios.get(`${API}/files`, { params: { db } });
