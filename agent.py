from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
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


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Charon",
            temperature=0.8,
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))