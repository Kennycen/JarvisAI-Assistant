from __future__ import annotations

import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

from livekit.agents import RunContext, function_tool

from jarvis.agent.deps import browser
from jarvis.core.errors import JarvisError

# Playwright is already async, so unlike the Google tools these await directly
# instead of going through asyncio.to_thread.

_RISKY_WORDS = frozenset(
    {"buy", "checkout", "confirm", "delete", "pay", "purchase", "remove", "send", "submit"}
)

# Set by confirm_browser_action and spent by the next matching click, so one
# confirmation authorizes exactly one consequential action.
_confirmed_target: str | None = None


def duckduckgo_search_url(query: str) -> str:
    query = query.strip()
    if not query:
        raise ValueError("The search query cannot be empty.")
    return f"https://duckduckgo.com/?{urlencode({'q': query})}"


def _requires_confirmation(target: str) -> bool:
    return bool(_RISKY_WORDS.intersection(target.casefold().split()))


@function_tool()
async def open_url(context: RunContext, url: str) -> str:
    """Open a webpage in the browser Jarvis controls.

    Prefer this over search_the_web whenever the user names a site, service, or domain.

    Args:
        url: A complete http or https URL.
    """
    try:
        page = await browser().open_url(url)
    except JarvisError as exc:
        return str(exc)
    return f"Opened '{page['title']}'. Read or inspect it before answering."


@function_tool()
async def search_the_web(context: RunContext, query: str) -> str:
    """Search DuckDuckGo, for general lookups where no particular site was named.

    Args:
        query: A concise search query carrying all the relevant context.
    """
    try:
        page = await browser().open_url(duckduckgo_search_url(query))
    except (JarvisError, ValueError) as exc:
        return str(exc)
    return f"Results are open: '{page['title']}'. Read the page before answering."


@function_tool()
async def read_page(context: RunContext) -> str:
    """Read the visible text of the current page."""
    try:
        result = await browser().read_page()
    except JarvisError as exc:
        return str(exc)

    suffix = " (truncated)" if result["truncated"] else ""
    return f"{result['title']}{suffix}\n\n{result['text']}"


@function_tool()
async def inspect_page(context: RunContext) -> str:
    """Read the current page and list the controls on it.

    Call this before click or type_text so the target names are real ones.
    """
    try:
        result = await browser().inspect_page()
    except JarvisError as exc:
        return str(exc)

    elements: list[dict] = result["elements"]  # type: ignore[assignment]
    controls = "\n".join(
        f"- {e['tag']}{'/' + e['role'] if e['role'] else ''}: {e['name']}"
        for e in elements
        if e["name"]
    )
    return f"{result['title']}\n\n{result['text']}\n\nControls:\n{controls or 'None found.'}"


@function_tool()
async def go_back(context: RunContext) -> str:
    """Go back to the previous page."""
    try:
        page = await browser().go_back()
    except JarvisError as exc:
        return str(exc)
    return f"Back on '{page['title']}'."


@function_tool()
async def take_screenshot(context: RunContext) -> str:
    """Save an image of the current page to disk, for diagnostics."""
    destination = Path(tempfile.gettempdir()) / "jarvis" / f"page-{int(time.time())}.png"
    try:
        result = await browser().take_screenshot(destination)
    except JarvisError as exc:
        return str(exc)
    return f"Captured '{result['title']}' to {result['path']}."


@function_tool()
async def click(context: RunContext, target: str) -> str:
    """Click a visible control by its accessible name.

    Args:
        target: The control's name, as returned by inspect_page.
    """
    global _confirmed_target

    if _requires_confirmation(target):
        if _confirmed_target != target.casefold():
            return (
                f"'{target}' looks consequential. Describe what will happen, get an "
                "explicit yes, then call confirm_browser_action before retrying."
            )
        _confirmed_target = None

    try:
        page = await browser().click(target)
    except JarvisError as exc:
        return str(exc)
    return f"Clicked '{target}'. Now on '{page['title']}'."


@function_tool()
async def confirm_browser_action(context: RunContext, target: str) -> str:
    """Authorize one consequential click the user has explicitly approved.

    Only call this after the user has clearly confirmed that exact action.

    Args:
        target: The exact control name the user approved.
    """
    global _confirmed_target

    _confirmed_target = target.casefold()
    return f"'{target}' is approved for one click."


@function_tool()
async def type_text(context: RunContext, target: str, text: str) -> str:
    """Fill a text field by its label, placeholder, or accessible name.

    Args:
        target: The field's label, placeholder, or accessible name.
        text: The text to enter.
    """
    try:
        await browser().type_text(target, text)
    except JarvisError as exc:
        return str(exc)
    return f"Typed into '{target}'."


@function_tool()
async def scroll(context: RunContext, direction: str) -> str:
    """Scroll the current page.

    Args:
        direction: Either 'up' or 'down'.
    """
    try:
        await browser().scroll(direction)  # type: ignore[arg-type]
    except JarvisError as exc:
        return str(exc)
    return f"Scrolled {direction}."


@function_tool()
async def press_key(context: RunContext, key: str) -> str:
    """Press a navigation key on the current page.

    Args:
        key: One of Enter, Escape, Tab, an arrow key, or Backspace.
    """
    try:
        await browser().press_key(key)
    except JarvisError as exc:
        return str(exc)
    return f"Pressed {key}."
