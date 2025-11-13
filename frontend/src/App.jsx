import VoiceInterface from "./components/VoiceInterface";
import "./App.css";
import CalendarAuth from "./components/CalendarAuth";

function App() {
  return (
    <div className="app">
      <div className="container">
        <h1>JARVIS Assistant</h1>
        <CalendarAuth />
        <VoiceInterface />
        <div className="info">
          <p>Features available:</p>
          <ul>
            <li>📧 Send emails</li>
            <li>📅 Manage Google Calendar</li>
            <li>🌤️ Weather information</li>
            <li>🔍 Web search</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
