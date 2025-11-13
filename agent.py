import logging
from dotenv import load_dotenv
import os
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import noise_cancellation, google, silero
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather, 
    search_web, 
    send_email, 
    open_chrome_tab, 
    open_tabs_sequentially,
    add_calendar_event_google,
    view_calendar_events_google,
    update_calendar_event_google,
    delete_calendar_event_google,
    list_all_events_google
)

logger = logging.getLogger("agent")
load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION, 
            tools=[
                get_weather, 
                search_web, 
                send_email, 
                open_chrome_tab, 
                open_tabs_sequentially,
                add_calendar_event_google,
                view_calendar_events_google,
                update_calendar_event_google,
                delete_calendar_event_google,
                list_all_events_google
            ]
        )


def prewarm(proc: JobProcess):
    pass


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Verify API key is set (plugin reads from GOOGLE_API_KEY automatically)
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        logger.error("GOOGLE_API_KEY not found in environment")
        raise ValueError(
            "GOOGLE_API_KEY environment variable is required. "
            "Get your API key from: https://aistudio.google.com/app/apikey"
        )
    
    logger.info("Initializing Google Gemini Realtime session")
    
    # Use google.realtime.RealtimeModel (NOT google.beta.realtime)
    # The plugin automatically reads GOOGLE_API_KEY from environment
    session = AgentSession(
        vad=silero.VAD.load(),
        llm=google.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Charon",
            temperature=0.8,
            instructions=SESSION_INSTRUCTION,  # Pass instructions here
        ),
    )

    await ctx.connect()

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Optional initial greeting but agent can responds when you talk first
    await session.generate_reply(instructions=SESSION_INSTRUCTION)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))