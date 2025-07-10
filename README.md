# ScheduleTools

Professional spreadsheet wrangling utilities for parsing, splitting, and expanding schedule data.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/scheduletools.svg)](https://badge.fury.io/py/scheduletools)

## Features

- **Flexible Parsing**: Parse schedule data from various formats with configurable date/time formats and block detection
- **Smart Splitting**: Split CSV data into multiple files based on grouping criteria with optional filtering
- **Column Expansion**: Transform data to match specific output formats with configurable mappings
- **Dual Interface**: Use as a Python library for programmatic access or as a CLI tool for file operations
- **Professional Design**: Clean API, comprehensive error handling, and type hints

## Installation

```bash
pip install scheduletools
```

For development installation:

```bash
git clone https://github.com/yourusername/scheduletools.git
cd scheduletools
pip install -e ".[dev]"
```

## Usage

### Programmatic Usage

```python
from scheduletools import ScheduleParser, CSVSplitter, ScheduleExpander
import pandas as pd

# Parse schedule with default settings
parser = ScheduleParser("schedule.txt", reference_date="2025-07-21")
parsed_data = parser.parse()

# Parse with custom configuration
custom_config = {
    "Format": {
        "Date": "%m/%d/%Y",
        "Time": "%I:%M %p"
    },
    "Block Detection": {
        "start_marker": "Date",
        "skip_meta_rows": True
    },
    "Missing Values": {
        "Omit": True,
        "Replacement": "TBD"
    }
}

parser = ScheduleParser(
    "schedule.txt", 
    reference_date="2025-07-21",
    config=custom_config
)
parsed_data = parser.parse()

# Split by team
splitter = CSVSplitter(parsed_data, "Team")
team_schedules = splitter.split()

# Expand with template
expander = ScheduleExpander(team_schedules["16U"], expansion_template)
expanded_data = expander.expand()
```

### As a CLI Tool

```bash
# Parse a schedule file with default block marker
schtool parse schedule.txt -o parsed_schedule.csv

# Parse with custom date column name
schtool parse schedule.txt --date-column "Day" -o parsed_schedule.csv

# Split by team
schtool split parsed_schedule.csv -g Team -o team_schedules/

# Expand with template
schtool expand team_schedules/Team_A.csv template.json -o final_schedule.csv

# Complete workflow
schtool process schedule.txt -o output/ -t template.json
```

## Documentation

### ScheduleParser

Parse schedule data from various formats into structured DataFrames.

```python
from scheduletools import ScheduleParser

# Basic usage with default date column name ("Date")
parser = ScheduleParser("schedule.txt")
df = parser.parse()

# With custom date column name
parser = ScheduleParser("schedule.txt", date_column_name="Day")
df = parser.parse()

# With custom configuration
parser = ScheduleParser(
    "schedule.txt",
    config_path="config.json",
    reference_date="2025-09-02",
    date_column_name="Day"
)
df = parser.parse()
```

**Configuration Format:**
```json
{
    "Format": {
        "Date": "%m/%d/%Y",
        "Time": "%I:%M %p",
        "Duration": "H:MM"
    },
    "Block Detection": {
        "date_column_name": "Date"
    },
    "Missing Values": {
        "Omit": true,
        "Replacement": "missing"
    },
    "Split": {
        "Skip": false,
        "Separator": "/"
    }
}
```

**Block Detection:**
The parser uses a configurable date column name to identify where schedule blocks begin. The `date_column_name` specifies the name of the date column (which is always the first column in each block). By default, it looks for "Date" in the first column of each row. When parsing blocks, rows without valid dates in the date column are automatically skipped.

### CSVSplitter

Split CSV data into multiple DataFrames based on grouping criteria.

```python
from scheduletools import CSVSplitter

# Split by single column
splitter = CSVSplitter("data.csv", "Team")
teams = splitter.split()

# Split by multiple columns with filtering
splitter = CSVSplitter(
    "data.csv", 
    ["Week", "Team"],
    include_values=["Week_1", "Week_2"],
    exclude_values=["Team_C"]
)
filtered_groups = splitter.split()
```

### ScheduleExpander

Expand schedule data to include required columns with mappings and defaults.

```python
from scheduletools import ScheduleExpander

# Expand with configuration
config = {
    "Required": ["Date", "Time", "Team", "Location", "Notes"],
    "defaults": {
        "Location": "Main Arena",
        "Notes": ""
    },
    "Mapping": {
        "Start Time": "Time",
        "Team Name": "Team"
    }
}

expander = ScheduleExpander("input.csv", config)
expanded_df = expander.expand()
```

## Configuration

ScheduleParser supports flexible configuration through config objects or JSON files. Configuration options include:

### Format Settings
- `Date`: Date format string (default: `"%m/%d/%Y"`)
- `Time`: Time format string (default: `"%I:%M %p"`)
- `Duration`: Duration format (default: `"H:MM"`)

### Block Detection
- `date_column_name`: Name of the date column that indicates the start of a block (default: `"Date"`)

### Missing Values
- `Omit`: Whether to omit missing values (default: `True`)
- `Replacement`: Value to use for missing entries (default: `"missing"`)

### Split Settings
- `Skip`: Whether to skip team splitting (default: `False`)
- `Separator`: Character to split team names (default: `"/"`)

### Example Configuration

```json
{
    "Format": {
        "Date": "%m/%d/%Y",
        "Time": "%I:%M %p",
        "Duration": "H:MM"
    },
    "Block Detection": {
        "date_column_name": "Date"
    },
    "Missing Values": {
        "Omit": true,
        "Replacement": "TBD"
    },
    "Split": {
        "Skip": false,
        "Separator": "/"
    }
}
```

## CLI Commands

### `schtool parse`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.3.0
- **Improved Field Naming**: Changed `start_marker` to `date_column_name` for better clarity
- **Dynamic Data Detection**: Replaced hard-coded row indices with automatic detection of where data starts
- **Optimized Parsing**: Combined block extraction and processing into a single efficient loop
- **Simplified Block Detection**: Removed meta pattern checking and `skip_meta_rows` configuration
- **Date-Only Validation**: Now only validates that the date column contains valid dates, automatically skipping invalid rows
- **Cleaner Configuration**: Simplified Block Detection section to only include `date_column_name`
- **Updated Documentation**: Clarified that `date_column_name` specifies the date column name

### 0.2.0
- **Enhanced Configuration System**: Added support for passing config objects directly to ScheduleParser
- **Improved Block Detection**: Fixed block boundary detection logic for more reliable parsing
- **Better Error Handling**: Enhanced error messages and exception handling for configuration files
- **Meta Row Detection**: Improved handling of empty strings and meta-information rows
- **Complete Workflow Support**: Fixed end-to-end workflow testing and validation
- **Documentation Updates**: Added comprehensive configuration documentation and examples

### 0.1.0
- Initial release
- Core parsing, splitting, and expansion functionality
- CLI interface with comprehensive commands
- Professional API design with type hints
- Comprehensive error handling
- Configurable block detection with custom markers