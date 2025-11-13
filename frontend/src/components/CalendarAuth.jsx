import { useState, useEffect } from "react";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CalendarAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/status`, {
        withCredentials: true,
      });
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error("Error checking auth status:", error);
    } finally {
      setLoading(false);
    }
  };

  const connectGoogle = () => {
    window.location.href = `${API_URL}/api/auth/google`;
  };

  const disconnect = async () => {
    try {
      await axios.post(
        `${API_URL}/api/auth/logout`,
        {},
        {
          withCredentials: true,
        }
      );
      setIsAuthenticated(false);
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  if (loading) {
    return <div>Checking authentication...</div>;
  }

  return (
    <div className="calendar-auth">
      {isAuthenticated ? (
        <div>
          <p>✅ Google Calendar connected</p>
          <button onClick={disconnect} className="btn btn-danger">
            Disconnect Calendar
          </button>
        </div>
      ) : (
        <div>
          <p>Connect Google Calendar to use calendar features</p>
          <button onClick={connectGoogle} className="btn btn-primary">
            Connect Google Calendar
          </button>
        </div>
      )}
    </div>
  );
};

export default CalendarAuth;
