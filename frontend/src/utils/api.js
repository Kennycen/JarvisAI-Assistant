import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const createRoom = async (participantName = "user") => {
  const response = await api.post("/api/create-room", {
    participant_name: participantName,
  });
  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get("/api/health");
  return response.data;
};

export default api;
