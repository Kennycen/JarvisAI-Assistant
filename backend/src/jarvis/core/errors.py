class JarvisError(Exception):
    """Base class for every error Jarvis raises deliberately."""


class AuthenticationError(JarvisError):
    """No Google account connected, or the stored token is no longer usable."""


class ServiceError(JarvisError):
    """A Google API call failed."""


class BrowserError(JarvisError):
    """A browser navigation or interaction step failed."""