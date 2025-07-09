"""
Custom exceptions for ScheduleTools package.
"""


class ScheduleToolsError(Exception):
    """Base exception for all ScheduleTools errors."""
    pass


class ParsingError(ScheduleToolsError):
    """Raised when there's an error parsing schedule data."""
    pass


class ValidationError(ScheduleToolsError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(ScheduleToolsError):
    """Raised when there's an error with configuration files or settings."""
    pass


class FileError(ScheduleToolsError):
    """Raised when there's an error reading or writing files."""
    pass 