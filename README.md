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

## Quick Start

### As a Python Library

```python
from scheduletools import ScheduleParser, CSVSplitter, ScheduleExpander

# Parse schedule data with default block marker
parser = ScheduleParser("schedule.txt")
parsed_data = parser.parse()

# Parse with custom block marker
parser = ScheduleParser("schedule.txt", block_start_marker="Day")
parsed_data = parser.parse()

# Split data by team
splitter = CSVSplitter(parsed_data, "Team")
team_schedules = splitter.split()

# Expand to required format
expander = ScheduleExpander(team_schedules["Team_A"], {
    "Required": ["Date", "Time", "Team", "Location", "Notes"],
    "defaults": {"Location": "Main Arena", "Notes": ""}
})
expanded_data = expander.expand()
```

### As a CLI Tool

```bash
# Parse a schedule file with default block marker
schtool parse schedule.txt -o parsed_schedule.csv

# Parse with custom block marker
schtool parse schedule.txt --block-marker "Day" -o parsed_schedule.csv

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

# Basic usage with default block marker ("Date")
parser = ScheduleParser("schedule.txt")
df = parser.parse()

# With custom block marker
parser = ScheduleParser("schedule.txt", block_start_marker="Day")
df = parser.parse()

# With custom configuration
parser = ScheduleParser(
    "schedule.txt",
    config_path="config.json",
    reference_date="2025-09-02",
    block_start_marker="Day"
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
        "start_marker": "Date",
        "skip_meta_rows": true,
        "meta_patterns": ["ice", "time", "header", "day", "week", "note", "info"]
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
The parser uses a configurable block marker to identify where schedule blocks begin. By default, it looks for "Date" in the first column of each row. You can customize this behavior:

- **`start_marker`**: Text that indicates the start of a block column (default: "Date")
- **`skip_meta_rows`**: Whether to skip rows containing meta-information
- **`meta_patterns`**: List of patterns to identify meta-information rows

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

## CLI Commands

### `schtool parse`

Parse a schedule file into structured CSV format.

```bash
# Use default block marker ("Date")
schtool parse schedule.txt -o parsed.csv

# Use custom block marker
schtool parse schedule.txt --block-marker "Day" -o parsed.csv

# With custom configuration
schtool parse schedule.txt --config config.json --reference-date 2025-09-02
```

### `schtool split`

Split CSV file into multiple files by group.

```bash
schtool split data.csv -g Team -o team_files/
schtool split data.csv -g "Week,Team" --filter "Week_1,Week_2" --exclude "Team_C"
```

### `schtool expand`

Expand schedule CSV to required column format.

```bash
schtool expand input.csv template.json -o expanded.csv
```

### `schtool process`

Complete workflow combining split and optional expand operations.

```bash
schtool process input.csv -o output/ -t template.json
```

## Input Format

The ScheduleParser expects tab-delimited files with a specific structure:

```
Monday		Tuesday			
Date	Time	Date	Time		
	6 pm - 7:15 pm		6:00 pm - 7:00 pm	7:00 pm - 8:00 pm	8:15 pm - 9:15 pm
7/21/2025	16U / 18U	7/22/2025	12U / 14U	18U	16U
7/28/2025	16U / 18U	7/29/2025	8U / 10U	18U	16U
8/4/2025	16U / 18U	8/5/2025	12U / 14U	18U	16U
```

**Key Features:**
- **Block Detection**: Uses configurable markers (default: "Date") to identify schedule blocks
- **Team Splitting**: Automatically splits combined teams (e.g., "16U / 18U" → separate entries)
- **Meta Row Handling**: Skips rows containing meta-information like "ice", "time", etc.
- **Flexible Format**: Supports different date/time formats via configuration

## Error Handling

The package provides comprehensive error handling with custom exceptions:

```python
from scheduletools import (
    ScheduleToolsError, 
    ParsingError, 
    ValidationError, 
    ConfigurationError, 
    FileError
)

try:
    parser = ScheduleParser("nonexistent.txt")
    df = parser.parse()
except FileError as e:
    print(f"File error: {e}")
except ParsingError as e:
    print(f"Parsing error: {e}")
```

## Development

### Setup

```bash
git clone https://github.com/yourusername/scheduletools.git
cd scheduletools
pip install -e ".[dev]"
```

### Testing

```bash
pytest
pytest --cov=scheduletools
```

### Code Quality

```bash
black scheduletools/
flake8 scheduletools/
mypy scheduletools/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0
- Initial release
- Core parsing, splitting, and expansion functionality
- CLI interface with comprehensive commands
- Professional API design with type hints
- Comprehensive error handling
- Configurable block detection with custom markers 