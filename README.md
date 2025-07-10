# ScheduleTools

A Python library for parsing, splitting, and expanding schedule data from various formats.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/scheduletools.svg)](https://badge.fury.io/py/scheduletools)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

- **ScheduleParser**: Parse tab-delimited schedule files with configurable date column names
- **ScheduleSplitter**: Split schedule data by groups and apply filters
- **ScheduleExpander**: Expand data to include required columns with mappings and defaults
- **CLI Interface**: Command-line tools for batch processing
- **Flexible Configuration**: JSON-based configuration with inheritance and validation

## Installation

```bash
pip install scheduletools
```

## Workflow Quick Start

```python
from scheduletools import ScheduleParser, ScheduleSplitter, ScheduleExpander

# 1. Parse schedule data
parser = ScheduleParser("schedule.txt")
parsed_data = parser.parse()

# 2. Split by team
splitter = ScheduleSplitter(parsed_data, "Team")
team_schedules = splitter.split()

# 3. Expand with additional columns
expander = ScheduleExpander(team_schedules["Team_A"], config.json)
expanded_data = expander.expand()
```

## Complete Workflow Example

This example demonstrates the full transformation from wide blocked schedules to long schedules, then expansion and splitting.

### Step 1: Parse Block Schedule

Start with a wide blocked schedule format:

| | | | | | |
|--|--|--|--|--|--|
| Date | Time | Date | Time | | |
| | 6 pm - 7:15 pm | | 6:00 pm - 7:00 pm | 7:00 pm - 8:00 pm | 8:15 pm - 9:15 pm |
| 7/21/2025 | 16U / 18U | 7/22/2025 | 12U / 14U | 18U | 16U |
| 7/28/2025 | 16U / 18U | 7/29/2025 | 8U / 10U | 18U | 16U |

```python
from scheduletools import ScheduleParser

# Parse with default "Date" column and reference date
parser = ScheduleParser("schedule.txt", reference_date="2025-07-21")
parsed_data = parser.parse()
```

**Output - Long Format Schedule:**

| Index | Week | Day | Date | Start Time | Duration | Team |
|-------|------|-----|------|------------|----------|------|
| 0 | 0 | Monday | 7/21/2025 | 6:00 PM | 1:15 | 16U |
| 1 | 0 | Monday | 7/21/2025 | 6:00 PM | 1:15 | 18U |
| 2 | 0 | Tuesday | 7/22/2025 | 6:00 PM | 1:00 | 12U |
| 3 | 0 | Tuesday | 7/22/2025 | 6:00 PM | 1:00 | 14U |
| 4 | 0 | Tuesday | 7/22/2025 | 7:00 PM | 1:00 | 18U |
| 5 | 0 | Tuesday | 7/22/2025 | 8:15 PM | 1:00 | 16U |
| 6 | 1 | Monday | 7/28/2025 | 6:00 PM | 1:15 | 16U |
| 7 | 1 | Monday | 7/28/2025 | 6:00 PM | 1:15 | 18U |
| 8 | 1 | Tuesday | 7/29/2025 | 6:00 PM | 1:00 | 8U |
| 9 | 1 | Tuesday | 7/29/2025 | 6:00 PM | 1:00 | 10U |
| 10 | 1 | Tuesday | 7/29/2025 | 7:00 PM | 1:00 | 18U |
| 11 | 1 | Tuesday | 7/29/2025 | 8:15 PM | 1:00 | 16U |

### Step 2: Expand with Required Fields

```python
from scheduletools import ScheduleExpander

# Configure expansion with required fields, defaults, and mappings
config = {
    "Required": [
        "Date",
        "Time", 
        "Duration",
        "Arrival Time",
        "Name",
        "Location Name",
        "Notes"
    ],
    "defaults": {
        "Name": "On-Ice Practice",
        "Location Name": "PISC",
        "Arrival Time": 15
    },
    "Mapping": {
        "Start Time": "Time",
        "Team": "Notes"
    }
}

expander = ScheduleExpander(parsed_data, config)
expanded_data = expander.expand()
```

**Output - Expanded Schedule:**

| Date | Time | Duration | Arrival Time | Name | Location Name | Notes |
|------|------|----------|--------------|------|---------------|-------|
| 7/21/2025 | 6:00 PM | 1:15 | 15 | On-Ice Practice | PISC | 16U |
| 7/21/2025 | 6:00 PM | 1:15 | 15 | On-Ice Practice | PISC | 18U |
| 7/22/2025 | 6:00 PM | 1:00 | 15 | On-Ice Practice | PISC | 12U |
| 7/22/2025 | 6:00 PM | 1:00 | 15 | On-Ice Practice | PISC | 14U |
| 7/22/2025 | 7:00 PM | 1:00 | 15 | On-Ice Practice | PISC | 18U |
| 7/22/2025 | 8:15 PM | 1:00 | 15 | On-Ice Practice | PISC | 16U |
| 7/28/2025 | 6:00 PM | 1:15 | 15 | On-Ice Practice | PISC | 16U |
| 7/28/2025 | 6:00 PM | 1:15 | 15 | On-Ice Practice | PISC | 18U |
| 7/29/2025 | 6:00 PM | 1:00 | 15 | On-Ice Practice | PISC | 8U |
| 7/29/2025 | 6:00 PM | 1:00 | 15 | On-Ice Practice | PISC | 10U |
| 7/29/2025 | 7:00 PM | 1:00 | 15 | On-Ice Practice | PISC | 18U |
| 7/29/2025 | 8:15 PM | 1:00 | 15 | On-Ice Practice | PISC | 16U |

### Step 3: Split by Team

```python
from scheduletools import ScheduleSplitter

# Split by the Notes column (which contains team names)
splitter = ScheduleSplitter(expanded_data, "Notes")
team_schedules = splitter.split()

# Show available team keys
print("Available teams:", list(team_schedules.keys()))
```

*Output:*

```terminal
Available teams:'10U', '12U', '14U', '16U', '18U', '8U'
```

**Example - Team 16U Schedule: `print(team_schedules['16U'])`**

| Date | Time | Duration | Arrival Time | Name | Location Name | Notes |
|------|------|----------|--------------|------|---------------|-------|
| 7/21/2025 | 6:00 PM | 1:15 | 15 | On-Ice Practice | PISC | 16U |
| 7/22/2025 | 8:15 PM | 1:00 | 15 | On-Ice Practice | PISC | 16U |
| 7/28/2025 | 6:00 PM | 1:15 | 15 | On-Ice Practice | PISC | 16U |
| 7/29/2025 | 8:15 PM | 1:00 | 15 | On-Ice Practice | PISC | 16U |

## ScheduleParser

Parse tab-delimited schedule files with flexible date column detection.

### Input Format

ScheduleParser expects tab-delimited files with blocks starting at rows containing your specified date column name (default: "Date"):

_Contents of `schedule.txt`:_

<div style="font-size:10pt;">

```text:schedule.txt
1|Monday      → Tuesday     →                    
2|Date        → Time        → Date         → Time        →             →            
3|            → 6:00–7:15pm →              → 6:00–7:00pm → 7:00–8:00pm → 8:15–9:15pm
4|7/21/2025   → 16U / 18U   → 7/22/2025    → 12U / 14U   → 18U         → 16U
5|7/28/2025   → 16U / 18U   → 7/29/2025    → 8U / 10U    → 18U         → 16U
6|8/04/2025   → 16U / 18U   → 8/05/2025    → 12U / 14U   → 18U         → 16U

```

_Note: `→` indicates an inserted tab._
</div>

### Usage

```python
from scheduletools import ScheduleParser

# Basic usage with default "Date" column name
parser = ScheduleParser("schedule.txt")
data = parser.parse()

# Custom date column name
parser = ScheduleParser("schedule.txt", date_column_name="Day")
data = parser.parse()

# With configuration file
parser = ScheduleParser("schedule.txt", config_path="config.json")
data = parser.parse()

# With config object
config = {"Format": {"Date": "%Y-%m-%d"}}
parser = ScheduleParser("schedule.txt", config=config)
data = parser.parse()
```

### Configuration

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
    "Separator": ","
  }
}
```

## ScheduleSplitter

Split schedule data into multiple DataFrames based on grouping criteria. ScheduleSplitter creates separate DataFrames for each unique combination of values in the specified grouping columns, making it easy to work with subsets of your data.

### Basic Usage

```python
from scheduletools import ScheduleSplitter

# Split by single column
splitter = ScheduleSplitter(df, "Team")
team_schedules = splitter.split()

# Split by multiple columns
splitter = ScheduleSplitter(df, ["Team", "Week"])
schedules = splitter.split()
```

### Advanced Usage

```python
from scheduletools import ScheduleSplitter

# With filtering
splitter = ScheduleSplitter(
    df, 
    "Team", 
    include_values=["Team_A", "Team_B"],
    exclude_values=["Team_C"]
)
filtered_schedules = splitter.split()
```

## ScheduleExpander

Expand schedule data to include required columns with mappings and defaults.

### Usage

```python
from scheduletools import ScheduleExpander

config = {
    "Required": ["Date", "Time", "Team", "Location", "Status"],
    "defaults": {
        "Location": "Main Arena",
        "Status": "Scheduled"
    },
    "Mapping": {
        "Start Time": "Time"
    }
}

expander = ScheduleExpander(data, config)
expanded_data = expander.expand()
```

## CLI Usage

```bash
# Parse schedule
scheduletools parse schedule.txt -o output.csv

# Split data
scheduletools split data.csv --groupby Team -o split/

# Expand data
scheduletools expand data.csv config.json -o expanded.csv
```

## Splitting Data

ScheduleSplitter provides powerful data splitting capabilities:

- **Dictionary Output**: Returns a dictionary where keys are group identifiers and values are DataFrames
- **Filtering**: Include or exclude specific values using `include_values` and `exclude_values` parameters
- **Multi-column Grouping**: Split by multiple columns simultaneously for complex data organization

## Changelog

### 0.3.2 
- Renamed `CSVSplitter` to `ScheduleSplitter` for better clarity
- Updated documentation to reflect the new class name
- Improved class descriptions to emphasize schedule data processing

### 0.3.0 
- Added configurable date column names (default: "Date")
- Improved block detection and parsing logic
- Added config object support for ScheduleParser
- Removed meta pattern validation, now only validates date column
- Combined block extraction and processing loops for better performance
- Enhanced error handling and validation

### 0.2.0 
- Added configurable block start markers
- Enhanced block detection strategies
- Added config object support
- Improved CLI integration
- Added comprehensive test coverage

### 0.1.0 
- Initial release
- Basic schedule parsing functionality
- CSV splitting capabilities
- Data expansion features