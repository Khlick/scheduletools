"""
ScheduleTools - Professional spreadsheet wrangling utilities.

A Python library for parsing, splitting, and expanding schedule data from various formats.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = "Khris Griffis, Ph.D."

from .core import ScheduleParser, ScheduleSplitter, ScheduleExpander
from .exceptions import ScheduleToolsError, ParsingError, ValidationError

__all__ = [
    "ScheduleParser",
    "ScheduleSplitter",
    "ScheduleExpander",
    "ScheduleToolsError",
    "ParsingError",
    "ValidationError",
]
