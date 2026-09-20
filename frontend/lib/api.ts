import axios from "axios";
import { supabase } from "@/contexts/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Refresh session if needed (Supabase handles this automatically)
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }

  return config;
});

// Response interceptor to handle 401 errors and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Get fresh session (Supabase automatically refreshes if needed)
        const {
          data: { session },
          error: refreshError,
        } = await supabase.auth.getSession();

        if (refreshError || !session?.access_token) {
          // If refresh fails, redirect to login
          processQueue(refreshError || new Error("No session"), null);
          isRefreshing = false;

          // Only redirect if we're in the browser
          if (typeof window !== "undefined") {
            window.location.href = "/login?error=session_expired";
          }

          return Promise.reject(refreshError || new Error("No session"));
        }

        // Update the original request with new token
        originalRequest.headers.Authorization = `Bearer ${session.access_token}`;

        // Process queued requests
        processQueue(null, session.access_token);
        isRefreshing = false;

        // Retry the original request
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        isRefreshing = false;

        // Redirect to login on refresh failure
        if (typeof window !== "undefined") {
          window.location.href = "/login?error=session_expired";
        }

        return Promise.reject(refreshErr);
      }
    }

    return Promise.reject(error);
  }
);

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
