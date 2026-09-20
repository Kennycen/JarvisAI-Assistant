-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Calendar credentials table (stores user's Google Calendar OAuth tokens)
CREATE TABLE IF NOT EXISTS calendar_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    credentials_json TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rooms table (links LiveKit rooms to users)
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    room_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_rooms_user_id ON rooms(user_id);
CREATE INDEX IF NOT EXISTS idx_rooms_room_name ON rooms(room_name);
CREATE INDEX IF NOT EXISTS idx_calendar_credentials_user_id ON calendar_credentials(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for calendar_credentials
CREATE TRIGGER update_calendar_credentials_updated_at 
    BEFORE UPDATE ON calendar_credentials 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
    

-- Email credentials table (stores user's Gmail OAuth tokens)
CREATE TABLE IF NOT EXISTS email_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    credentials_json TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_credentials_user_id ON email_credentials(user_id);

CREATE TRIGGER update_email_credentials_updated_at 
    BEFORE UPDATE ON email_credentials 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();