# JARVIS Assistant

A sophisticated AI personal assistant inspired by Tony Stark's J.A.R.V.I.S, built with LiveKit Agents and Google's Gemini AI. JARVIS can manage your calendar, send emails, search the web, control your browser, and provide weather information with a witty British butler personality.

## ✨ Features

- **Calendar Management**: Full Google Calendar integration (add, view, update, delete events)
- **Email System**: Send emails via Gmail SMTP
- **Web Search**: DuckDuckGo-powered web search
- **Weather Updates**: Real-time weather information for any city
- **Browser Control**: Open websites and manage Chrome tabs
- **Personality**: Witty British butler personality with dry humor

---

# Terminal 1 — API, mints LiveKit tokens

cd backend && uv run uvicorn jarvis.api.main:app --port 8000

# Terminal 2 — agent worker, this IS Jarvis

cd backend && uv run python -m jarvis.agent.worker dev

# Terminal 3 — frontend

cd frontend && npm run dev
