# JARVIS Assistant

A sophisticated AI personal assistant inspired by Tony Stark's J.A.R.V.I.S, built with LiveKit Agents and Google's Gemini AI. JARVIS can manage your calendar, send emails, search the web, control your browser, and provide weather information with a witty British butler personality.

## ✨ Features

- **Voice Interaction**: Real-time voice conversations with Google's Gemini 2.0 Flash
- **Calendar Management**: Full Google Calendar integration (add, view, update, delete events)
- **Email System**: Send emails via Gmail SMTP
- **Web Search**: DuckDuckGo-powered web search
- **Weather Updates**: Real-time weather information for any city
- **Browser Control**: Open websites and manage Chrome tabs
- **Personality**: Witty British butler personality with dry humor

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- Google Chrome browser (for web navigation features)
- Google Cloud Console account
- Gmail account with App Password
- LiveKit Cloud account

### Installation

1. **Clone the repository**

   git clone https://github.com/yourusername/jarvis-assistant.git
   cd jarvis-assistant
   2. **Set up Python environment**

   
   ### Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: ai\Scripts\activate

   ### Install Python dependencies
   pip install -r requirements.txt
   3. **Set up Node.js environment**

   ### Navigate to client directory
   cd client

   ### Install Node.js dependencies
   npm install

   ### Return to root directory
   cd ..
   4. **Set up environment variables**

   ### Copy the example environment file
   cp .env.example .env

   ### Edit the .env file with your actual credentials
   nano .env  # or use your preferred editor
      **Required variables to configure:**

   - `LIVEKIT_API_KEY` - Your LiveKit Cloud API key
   - `LIVEKIT_API_SECRET` - Your LiveKit Cloud API secret
   - `LIVEKIT_URL` - Your LiveKit Cloud WebSocket URL
   - `GMAIL_USER` - Your Gmail address
   - `GMAIL_APP_PASSWORD` - Your Gmail App Password
   - `GOOGLE_API_KEY` - Your Google AI Studio API key
   - `GOOGLE_CLOUD_PROJECT_ID` - Your Google Cloud Project ID
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_ANON_KEY` - Your Supabase anonymous key
   - `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
   - `SECRET_KEY` - Secret key for session management

## Configuration

### 1. Google Calendar Setup

1. **Create Google Cloud Project**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Calendar API

2. **Create OAuth 2.0 Credentials**

   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the credentials file as `credentials.json`
   - Place it in the project root directory

3. **Generate Access Token**

   
   python -c "
   from google_auth_oauthlib.flow import InstalledAppFlow
   from google.oauth2.credentials import Credentials

   SCOPES = ['https://www.googleapis.com/auth/calendar']
   flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
   creds = flow.run_local_server(port=0)

   with open('token.json', 'w') as token:
       token.write(creds.to_json())
   print('Token generated successfully!')
   "
   
   **Note**: After generating the token, you can delete `credentials.json` as the system will use `token.json` for future authentication.

### 2. Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Generate password for "Mail"
   - Use this password in your `.env` file

### 3. LiveKit Cloud Setup

1. **Create LiveKit Cloud Account**

   - Sign up at [LiveKit Cloud](https://cloud.livekit.io/)
   - Create a new project

2. **Get API Credentials**
   - Copy your API Key, API Secret, and WebSocket URL
   - Add them to your `.env` file

## 🎯 Usage

### Starting All Services

The JARVIS Assistant consists of 3 services that need to be running:

1. **Agent Service** (Python) - The main JARVIS AI agent
2. **Server Service** (FastAPI) - Backend API server
3. **Client Service** (Next.js) - Frontend web application

#### Option 1: Run in Separate Terminals

**Terminal 1 - Agent Service:**
# Activate virtual environment
source venv/bin/activate  # On Windows: ai\Scripts\activate

# Start the JARVIS agent
python agent.py dev

**Terminal 2 - Server Service:**

# Start the FastAPI server
uvicorn server.main:app --reload

**Terminal 3 - Client Service:**
# Navigate to client directory
cd client

# Start the Next.js development server
npm run dev

### Accessing the Application

Once all services are running:
- **Frontend**: Open `http://localhost:3000` in your browser
- **Backend**: Visit `http://localhost:8000` in your browser
