"""Custom exceptions for tools"""

class ToolError(Exception):
    """Base exception for tool errors"""
    pass

class AuthenticationError(ToolError):
    """Raised when authentication fails"""
    pass

class ConfigurationError(ToolError):
    """Raised when required configuration is missing"""
    pass

class APIError(ToolError):
    """Raised when external API calls fail"""
    pass