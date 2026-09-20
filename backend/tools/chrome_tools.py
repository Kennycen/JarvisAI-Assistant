import logging
import subprocess
import platform
import os
import asyncio
from typing import Optional, List
from livekit.agents import function_tool, RunContext

# Website mapping (keeping your existing one)
WEBSITE_MAP = {
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "instagram": "https://www.instagram.com",
    "ig": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "amazon": "https://www.amazon.com",
    "gmail": "https://mail.google.com",
    "drive": "https://drive.google.com",
    "google": "https://www.google.com",
    "stackoverflow": "https://stackoverflow.com",
    "so": "https://stackoverflow.com",
    "discord": "https://discord.com",
    "twitch": "https://www.twitch.tv",
    "tiktok": "https://www.tiktok.com",
    "linkedin": "https://www.linkedin.com",
    "slack": "https://slack.com",
    "zoom": "https://zoom.us",
    "teams": "https://teams.microsoft.com",
    "trello": "https://trello.com",
    "notion": "https://www.notion.so",
    "wikipedia": "https://www.wikipedia.org",
    "wiki": "https://www.wikipedia.org",
    "cnn": "https://www.cnn.com",
    "bbc": "https://www.bbc.com",
    "paypal": "https://www.paypal.com",
    "robinhood": "https://robinhood.com",
    "coinbase": "https://www.coinbase.com",
}

def get_chrome_path() -> Optional[str]:
    """Get the Chrome executable path based on the operating system."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Windows":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    else:  # Linux
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

def clean_url_input(url: str) -> str:
    """Clean and extract the website name from user input."""
    url = url.strip().lower()
    
    prefixes = [
        "open ", "go to ", "visit ", "navigate to ", "take me to ",
        "launch ", "start ", "bring up ", "show me ", "pull up ",
        "can you open ", "please open ", "open a tab for "
    ]
    
    for prefix in prefixes:
        if url.startswith(prefix):
            url = url[len(prefix):].strip()
    
    return url

def get_final_url(url: str) -> str:
    """Convert any input to a proper URL."""
    clean_url = clean_url_input(url)
    
    if clean_url.startswith(('http://', 'https://')):
        return clean_url
    
    if clean_url in WEBSITE_MAP:
        return WEBSITE_MAP[clean_url]
    
    if '.' in clean_url:
        if not clean_url.startswith('www.'):
            return f"https://{clean_url}"
        else:
            return f"https://{clean_url}"
    
    return f"https://www.google.com/search?q={clean_url}"

@function_tool()
async def open_chrome_tab(
    context: RunContext,  # type: ignore
    url: str
) -> str:
    """
    MANDATORY BROWSER CONTROL - Open a single URL in Chrome browser immediately.
    
    TRIGGER WORDS (use this tool when user says ANY of these):
    - "open [website]"
    - "go to [website]" 
    - "visit [website]"
    - "launch [website]"
    - "navigate to [website]"
    - "pull up [website]"
    - "show me [website]"
    
    Args:
        url: Website name or URL to open (e.g., "youtube", "github.com", "https://example.com")
    
    Sir expects immediate browser execution when web navigation is requested.
    """
    try:
        print(f"🌐 JARVIS BROWSER SYSTEM: Opening {url}")
        logging.info(f"Opening Chrome tab for: {url}")
        
        final_url = get_final_url(url)
        print(f"🌐 Final URL: {final_url}")
        
        chrome_path = get_chrome_path()
        if not chrome_path:
            return "Chrome browser not found on this system, Sir."
        
        # Use a single command to open Chrome with the URL
        if platform.system() == "Darwin":  # macOS
            # Use 'open' command which is more reliable on macOS
            cmd = ['open', '-na', 'Google Chrome', '--args', '--new-tab', final_url]
        elif platform.system() == "Windows":
            cmd = [chrome_path, '--new-tab', final_url]
        else:  # Linux
            cmd = [chrome_path, '--new-tab', final_url]
        
        print(f"🌐 Executing: {' '.join(cmd)}")
        
        # Execute with timeout
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        )
        
        if result.returncode == 0:
            print(f"🌐 SUCCESS: Opened {final_url}")
            return f"Browser launched with {final_url}, Sir."
        else:
            print(f"🌐 FAILED: {result.stderr}")
            return f"Browser launch failed: {result.stderr}"
            
    except asyncio.TimeoutError:
        print("🌐 TIMEOUT: Chrome launch timed out")
        return "Browser launch timed out, Sir."
    except Exception as e:
        print(f"🌐 ERROR: {e}")
        return f"Browser system error: {str(e)}"

@function_tool()
async def open_multiple_tabs(
    context: RunContext,  # type: ignore
    urls: List[str]
) -> str:
    """
    MANDATORY MULTI-BROWSER CONTROL - Open multiple URLs in Chrome tabs simultaneously.
    
    TRIGGER PHRASES:
    - "open [site1] and [site2]" 
    - "launch [site1], [site2], and [site3]"
    - "go to [site1] and [site2]"
    - "open multiple tabs with [sites]"
    - "visit [site1], [site2]"
    
    Args:
        urls: List of website names or URLs to open
    
    JARVIS will launch all requested sites efficiently in separate tabs.
    """
    try:
        if not urls:
            return "No websites specified for launch, Sir."
        
        print(f"🌐 JARVIS MULTI-BROWSER: Opening {len(urls)} tabs")
        logging.info(f"Opening multiple Chrome tabs: {urls}")
        
        # Limit tabs to prevent system overload
        max_tabs = 8
        if len(urls) > max_tabs:
            urls = urls[:max_tabs]
            print(f"🌐 Limited to {max_tabs} tabs for system stability")
        
        chrome_path = get_chrome_path()
        if not chrome_path:
            return "Chrome browser not found on this system, Sir."
        
        # Process all URLs
        final_urls = [get_final_url(url) for url in urls]
        print(f"🌐 Final URLs: {final_urls}")
        
        # BETTER APPROACH: Open all tabs in a single Chrome command
        if platform.system() == "Darwin":  # macOS
            # Open Chrome first, then add tabs
            base_cmd = ['open', '-na', 'Google Chrome', '--args']
            for url in final_urls:
                base_cmd.extend(['--new-tab', url])
            cmd = base_cmd
        elif platform.system() == "Windows":
            # Open all URLs in one command
            cmd = [chrome_path] + [item for url in final_urls for item in ['--new-tab', url]]
        else:  # Linux  
            cmd = [chrome_path] + [item for url in final_urls for item in ['--new-tab', url]]
        
        print(f"🌐 Executing multi-tab command")
        
        # Execute the command
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        )
        
        if result.returncode == 0:
            print(f"🌐 SUCCESS: Opened {len(final_urls)} tabs")
            return f"Launched {len(final_urls)} browser tabs successfully, Sir:\n" + "\n".join([f"• {url}" for url in final_urls])
        else:
            print(f"🌐 PARTIAL SUCCESS: Some tabs may have opened")
            # Even if return code isn't 0, Chrome often still opens the tabs
            return f"Browser launched with {len(final_urls)} tabs (some warnings occurred), Sir."
            
    except asyncio.TimeoutError:
        print("🌐 TIMEOUT: Multi-tab launch timed out")
        return "Multi-tab browser launch timed out, Sir."
    except Exception as e:
        print(f"🌐 ERROR: {e}")
        return f"Multi-browser system error: {str(e)}"

# Alternative simpler approach for multiple tabs
@function_tool()
async def open_tabs_sequentially(
    context: RunContext,  # type: ignore  
    urls: List[str]
) -> str:
    """
    ALTERNATIVE BROWSER CONTROL - Open multiple tabs one by one with delays.
    Use this if open_multiple_tabs fails.
    
    Args:
        urls: List of website names or URLs to open sequentially
    """
    try:
        if not urls:
            return "No websites specified, Sir."
        
        print(f"🌐 JARVIS SEQUENTIAL BROWSER: Opening {len(urls)} tabs sequentially")
        
        successful_tabs = 0
        results = []
        
        for i, url in enumerate(urls[:5]):  # Limit to 5 for sequential approach
            try:
                print(f"🌐 Opening tab {i+1}/{len(urls)}: {url}")
                
                final_url = get_final_url(url)
                chrome_path = get_chrome_path()
                
                if not chrome_path:
                    results.append(f"{url}: Chrome not found")
                    continue
                
                if platform.system() == "Darwin":
                    cmd = ['open', '-na', 'Google Chrome', '--args', '--new-tab', final_url]
                else:
                    cmd = [chrome_path, '--new-tab', final_url]
                
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                )
                
                if result.returncode == 0:
                    successful_tabs += 1
                    results.append(f"✓ {url}")
                    print(f"🌐 SUCCESS: Tab {i+1}")
                else:
                    results.append(f"✗ {url}")
                    print(f"🌐 FAILED: Tab {i+1}")
                
                # Wait between tabs
                if i < len(urls) - 1:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                results.append(f"✗ {url}: {str(e)}")
                print(f"🌐 ERROR on tab {i+1}: {e}")
        
        return f"Sequential launch complete: {successful_tabs}/{len(urls)} tabs opened, Sir.\n" + "\n".join(results)
        
    except Exception as e:
        print(f"🌐 SEQUENTIAL ERROR: {e}")
        return f"Sequential browser system error: {str(e)}"