"""
ScheduleTools - Professional spreadsheet wrangling utilities

A Python package for parsing, splitting, and expanding schedule data
with both CLI and programmatic interfaces.
"""

__version__ = "0.3.2"
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
