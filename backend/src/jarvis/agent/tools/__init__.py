from jarvis.agent.tools.browser import (
    click,
    confirm_browser_action,
    go_back,
    inspect_page,
    open_url,
    press_key,
    read_page,
    scroll,
    search_the_web,
    take_screenshot,
    type_text,
)
from jarvis.agent.tools.calendar import create_event, delete_event, list_events
from jarvis.agent.tools.gmail import (
    archive_email,
    draft_email,
    read_email,
    search_email,
    send_email,
    trash_email,
)

ALL_TOOLS = [
    search_email,
    read_email,
    draft_email,
    send_email,
    archive_email,
    trash_email,
    list_events,
    create_event,
    delete_event,
    # open_url leads so the model reaches for a named site before falling back to search.
    open_url,
    search_the_web,
    read_page,
    inspect_page,
    go_back,
    take_screenshot,
    click,
    confirm_browser_action,
    type_text,
    scroll,
    press_key,
]

__all__ = ["ALL_TOOLS"]
