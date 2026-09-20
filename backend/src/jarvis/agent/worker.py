from __future__ import annotations

import logging

from dotenv import load_dotenv
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, room_io
from livekit.plugins import google

from jarvis.agent.deps import browser, profile
from jarvis.agent.prompts import JARVIS_INSTRUCTIONS, render_profile_section
from jarvis.agent.tools import ALL_TOOLS
from jarvis.config import PROJECT_ROOT, get_settings

# The Google plugin reads GOOGLE_API_KEY straight from the process environment.
load_dotenv(PROJECT_ROOT / ".env.local")

logger = logging.getLogger("jarvis")

AGENT_NAME = "jarvis"


class Jarvis(Agent):
    def __init__(self, instructions: str = JARVIS_INSTRUCTIONS) -> None:
        super().__init__(instructions=instructions, tools=ALL_TOOLS)


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def jarvis_session(ctx: JobContext) -> None:
    get_settings()  # fail loudly now if configuration is incomplete
    ctx.log_context_fields = {"room": ctx.room.name}

    # The browser starts lazily on first use; this closes it if a session ever opened one.
    ctx.add_shutdown_callback(browser().close)

    # Read per session, so editing the profile in the sidebar takes effect on the
    # next session rather than needing a worker restart.
    instructions = JARVIS_INSTRUCTIONS + render_profile_section(profile())

    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            voice="Charon",
            temperature=0.8,
            # Native-audio only: lets the model modulate tone and emotion.
            enable_affective_dialog=True,
        ),
    )

    await session.start(
        agent=Jarvis(instructions),
        room=ctx.room,
        # text_input lets the React chat panel talk to the same session over lk.chat.
        room_options=room_io.RoomOptions(text_input=True, text_output=True),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)