"""
Core classes for ScheduleTools package.

This module provides the main classes for parsing, splitting, and expanding
schedule data. These classes are designed to be used both programmatically
and through the CLI interface.
"""

import pandas as pd
import json
import warnings
import re
import os
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path

from .exceptions import (
    ScheduleToolsError, 
    ParsingError, 
    ValidationError, 
    ConfigurationError, 
    FileError
)


class ScheduleParser:
    """
    Parse schedule data from various formats into structured DataFrames.
    
    This class handles the parsing of schedule data with configurable
    date/time formats and data cleaning options.
    """
    
    DEFAULT_CONFIG = {
        "Format": {
            "Date": "%m/%d/%Y",
            "Time": "%I:%M %p",
            "Duration": "H:MM"
        },
        "Block Detection": {
            "start_marker": "Date",
            "skip_meta_rows": True,
            "meta_patterns": ["ice", "time", "header", "day", "week", "note", "info"]
        },
        "Missing Values": {
            "Omit": True,
            "Replacement": "missing"
        },
        "Split": {
            "Skip": False,
            "Separator": "/"
        }
    }

    def __init__(
        self, 
        schedule_path: Union[str, Path], 
        config_path: Optional[Union[str, Path]] = None, 
        reference_date: str = "2025-09-02",
        block_start_marker: Optional[str] = None
    ):
        """
        Initialize the ScheduleParser.
        
        Args:
            schedule_path: Path to the schedule file
            config_path: Optional path to configuration JSON file
            reference_date: Reference date for week calculations
            block_start_marker: Text marker that indicates the start of a block column (default: "Date")
        """
        self.schedule_path = Path(schedule_path)
        self.reference_date = pd.to_datetime(reference_date)
        self.block_start_marker = block_start_marker
        self.config = self._load_config(config_path)
        self._validate_config()
        
    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileError(f"Configuration file not found: {config_path}")
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in config file: {e}")
        
        # Try fallback config
        fallback_path = self.schedule_path.parent / "parser_config.json"
        if fallback_path.exists():
            try:
                with open(fallback_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                warnings.warn("Fallback config file is invalid, using defaults")
        
        return self.DEFAULT_CONFIG.copy()
    
    def _validate_config(self) -> None:
        """Validate the configuration structure."""
        required_keys = ["Format", "Missing Values", "Split"]
        for key in required_keys:
            if key not in self.config:
                raise ConfigurationError(f"Missing required config key: {key}")
        
        # Ensure Block Detection section exists
        if "Block Detection" not in self.config:
            self.config["Block Detection"] = self.DEFAULT_CONFIG["Block Detection"]
    
    def _is_meta_row(self, value: str) -> bool:
        """Check if a row value is meta-information that should be skipped."""
        if pd.isna(value):
            return True
        
        value_str = str(value).lower().strip()
        meta_patterns = self.config["Block Detection"].get("meta_patterns", [])
        
        return any(pattern in value_str for pattern in meta_patterns)
    
    def _find_block_boundaries(self) -> List[Tuple[int, int]]:
        """
        Find block boundaries based on the configurable marker.
        
        Returns:
            List of (start_col, end_col) tuples for each block
        """
        df = self.df
        
        # Use configurable block start marker
        block_marker = self.block_start_marker or self.config["Block Detection"]["start_marker"]
        
        # Find the row that contains the block start marker in the first column
        marker_row_idx = None
        for row_idx, row in df.iterrows():
            first_col_value = str(row.iloc[0]).strip().lower()
            if first_col_value == block_marker.lower():
                marker_row_idx = row_idx
                break
        
        if marker_row_idx is None:
            raise ParsingError(f"No block start marker '{block_marker}' found in first column")
        
        # Use that row to find block boundaries
        marker_row = df.iloc[marker_row_idx]
        block_start_cols = []
        
        # Find all columns in this row that contain the block marker
        for col_idx, value in enumerate(marker_row):
            if str(value).strip().lower() == block_marker.lower():
                block_start_cols.append(col_idx)
        
        if not block_start_cols:
            raise ParsingError(f"No block start marker '{block_marker}' found in row {marker_row_idx}")
        
        # Create blocks from each start column
        blocks = []
        for i, start_col in enumerate(block_start_cols):
            # Determine end column for this block
            if i < len(block_start_cols) - 1:
                # Block ends at the start of the next block
                end_col = block_start_cols[i + 1]
            else:
                # Last block extends to the end
                end_col = df.shape[1]
            
            blocks.append((start_col, end_col))
        
        return blocks
    
    def _parse_time_and_duration(self, interval: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse time interval string into start time and duration."""
        interval = interval.strip()
        if "Time" in interval or not interval or "-" not in interval:
            warnings.warn(f"⚠️  Skipping invalid or label interval: '{interval}'")
            return None, None

        try:
            start_str, end_str = interval.lower().split("-")
            start_str = start_str.strip()
            end_str = end_str.strip()

            time_format_attempts = ["%I %p", "%I:%M %p"]
            start_dt = end_dt = None

            for fmt in time_format_attempts:
                try:
                    start_dt = pd.to_datetime(start_str, format=fmt)
                    break
                except Exception:
                    continue
            for fmt in time_format_attempts:
                try:
                    end_dt = pd.to_datetime(end_str, format=fmt)
                    break
                except Exception:
                    continue

            if not start_dt or not end_dt:
                raise ValueError("Could not parse time.")

            if end_dt < start_dt:
                end_dt += pd.Timedelta(days=1)

            duration = end_dt - start_dt
            duration_str = f"{int(duration.total_seconds() // 3600)}:{int((duration.total_seconds() % 3600) // 60):02}"
            return start_dt.strftime(self.config["Format"]["Time"]).lstrip("0"), duration_str
        except Exception:
            warnings.warn(f"⚠️  Failed to parse interval: '{interval}'")
            return None, None

    def _parse_block(self, block: pd.DataFrame, block_info: dict) -> pd.DataFrame:
        """
        Parse a single block with better meta-information handling.
        
        Args:
            block: DataFrame containing the block data
            block_info: Dictionary with block metadata (marker_row_idx, start_col, end_col, etc.)
        """
        date_col = block.columns[0]
        dates = block[date_col].iloc[3:].reset_index(drop=True)  # Skip meta rows
        rows = []
        
        # Get time intervals from the row after the block start marker
        marker_row_idx = block_info['marker_row_idx']
        time_row_idx = marker_row_idx + 1
        
        for col in block.columns[1:]:
            time_interval = block.iloc[time_row_idx, block.columns.get_loc(col)]
            if pd.isna(time_interval):
                continue

            start_time, duration = self._parse_time_and_duration(time_interval)
            if not (start_time and duration):
                continue

            # Process team entries, skipping meta rows
            for i, team_entry in enumerate(block[col].iloc[3:].reset_index(drop=True)):
                date_str = dates.iloc[i]
                if pd.isna(date_str) or self._is_meta_row(date_str):
                    continue

                try:
                    date_obj = pd.to_datetime(str(date_str), format=self.config["Format"]["Date"])
                except Exception:
                    continue

                team_str = str(team_entry).strip() if not pd.isna(team_entry) else ''
                if not team_str:
                    if self.config["Missing Values"]["Omit"]:
                        continue
                    team_list = [self.config["Missing Values"]["Replacement"]]
                else:
                    if self.config["Split"]["Skip"]:
                        team_list = [team_str]
                    else:
                        team_list = [t.strip() for t in re.split(rf"{re.escape(self.config['Split']['Separator'])}", team_str) if t.strip()]

                for team in team_list:
                    rows.append({
                        "Week": (date_obj - self.reference_date).days // 7,
                        "Day": date_obj.strftime("%A"),
                        "Date": date_obj.strftime(self.config["Format"]["Date"]),
                        "Start Time": start_time,
                        "Duration": duration,
                        "Team": team
                    })

        return pd.DataFrame(rows)

    def parse(self) -> pd.DataFrame:
        """
        Parse the schedule file and return a structured DataFrame.
        
        Returns:
            DataFrame with parsed schedule data
            
        Raises:
            FileError: If the schedule file cannot be read
            ParsingError: If there's an error parsing the data
        """
        if not self.schedule_path.exists():
            raise FileError(f"Schedule file not found: {self.schedule_path}")
        
        try:
            self.df = pd.read_csv(self.schedule_path, sep="\t", header=None)
        except Exception as e:
            raise FileError(f"Error reading schedule file: {e}")
        
        try:
            # Find block boundaries using configurable marker
            block_boundaries = self._find_block_boundaries()
            
            if not block_boundaries:
                raise ParsingError("No valid blocks found in schedule data")

            # Find the marker row index
            block_marker = self.block_start_marker or self.config["Block Detection"]["start_marker"]
            marker_row_idx = None
            for row_idx, row in self.df.iterrows():
                first_col_value = str(row.iloc[0]).strip().lower()
                if first_col_value == block_marker.lower():
                    marker_row_idx = row_idx
                    break

            blocks = []
            for start_col, end_col in block_boundaries:
                # Extract the block data - these are column indices
                subset = self.df.iloc[:, start_col:end_col].copy()
                
                # Filter out rows that don't have data in the first column
                mask = pd.Series(True, index=subset.index)
                mask[3:] = pd.notna(subset.iloc[3:, 0])
                subset = subset[mask]
                
                block_info = {
                    'marker_row_idx': marker_row_idx,
                    'start_col': start_col,
                    'end_col': end_col
                }
                blocks.append((subset, block_info))

            dfs = []
            for block, block_info in blocks:
                parsed_block = self._parse_block(block, block_info)
                if not parsed_block.empty:
                    dfs.append(parsed_block)

            if not dfs:
                return pd.DataFrame()

            result = pd.concat(dfs, ignore_index=True)
            result["Date"] = pd.to_datetime(result["Date"], format=self.config["Format"]["Date"])
            result = result.sort_values(["Date", "Start Time"]).reset_index(drop=True)
            result["Date"] = result["Date"].dt.strftime(self.config["Format"]["Date"])
            result.index.name = "Index"
            result.reset_index(inplace=True)
            return result
            
        except Exception as e:
            raise ParsingError(f"Error parsing schedule data: {e}")


class CSVSplitter:
    """
    Split CSV data into multiple DataFrames based on grouping criteria.
    
    This class provides functionality to split data by groups and optionally
    filter the results.
    """
    
    def __init__(
        self, 
        data: Union[pd.DataFrame, str, Path],
        group_columns: Union[str, List[str]],
        include_values: Optional[Union[str, List[str]]] = None,
        exclude_values: Optional[Union[str, List[str]]] = None
    ):
        """
        Initialize the CSVSplitter.
        
        Args:
            data: DataFrame or path to CSV file
            group_columns: Column(s) to group by
            include_values: Optional values to include (filter)
            exclude_values: Optional values to exclude (filter)
        """
        self.data = self._load_data(data)
        self.group_columns = self._normalize_columns(group_columns)
        self.include_values = self._normalize_values(include_values)
        self.exclude_values = self._normalize_values(exclude_values)
        
        self._validate_inputs()
    
    def _load_data(self, data: Union[pd.DataFrame, str, Path]) -> pd.DataFrame:
        """Load data from DataFrame or file path."""
        if isinstance(data, pd.DataFrame):
            return data.copy()
        elif isinstance(data, (str, Path)):
            path = Path(data)
            if not path.exists():
                raise FileError(f"Input file not found: {path}")
            try:
                return pd.read_csv(path)
            except Exception as e:
                raise FileError(f"Error reading CSV file: {e}")
        else:
            raise ValidationError("Data must be a DataFrame or file path")
    
    def _normalize_columns(self, columns: Union[str, List[str]]) -> List[str]:
        """Normalize column specification to list of strings."""
        if isinstance(columns, str):
            return [col.strip() for col in columns.split(",")]
        elif isinstance(columns, list):
            return [str(col).strip() for col in columns]
        else:
            raise ValidationError("Group columns must be a string or list")
    
    def _normalize_values(self, values: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
        """Normalize filter values to list of strings."""
        if values is None:
            return None
        if isinstance(values, str):
            return [v.strip() for v in values.split(",")]
        elif isinstance(values, list):
            return [str(v).strip() for v in values]
        else:
            raise ValidationError("Filter values must be a string or list")
    
    def _validate_inputs(self) -> None:
        """Validate that all specified columns exist in the data."""
        missing_cols = [col for col in self.group_columns if col not in self.data.columns]
        if missing_cols:
            raise ValidationError(f"Group columns not found in data: {missing_cols}")
    
    def _should_include(self, group_keys: Union[Any, Tuple[Any, ...]]) -> bool:
        """Check if a group should be included based on filters."""
        keys = [str(k) for k in group_keys] if isinstance(group_keys, tuple) else [str(group_keys)]

        if self.include_values and not any(k in self.include_values for k in keys):
            return False
        if self.exclude_values and any(k in self.exclude_values for k in keys):
            return False
        return True

    def split(self) -> Dict[str, pd.DataFrame]:
        """
        Split the data into multiple DataFrames based on grouping criteria.
        
        Returns:
            Dictionary mapping group keys to DataFrames
        """
        grouped = self.data.groupby(self.group_columns)
        result = {}
        
        for group_keys, group_df in grouped:
            if not self._should_include(group_keys):
                continue
                
            # Create a key for the dictionary
            if isinstance(group_keys, tuple):
                key = "_".join(str(k).replace(" ", "_") for k in group_keys)
            else:
                key = str(group_keys).replace(" ", "_")
            
            result[key] = group_df.reset_index(drop=True)
        
        return result


class ScheduleExpander:
    """
    Expand schedule data to include required columns with mappings and defaults.
    
    This class handles the transformation of schedule data to match
    specific output formats with configurable column mappings.
    """
    
    def __init__(
        self, 
        data: Union[pd.DataFrame, str, Path],
        config: Union[Dict[str, Any], str, Path]
    ):
        """
        Initialize the ScheduleExpander.
        
        Args:
            data: DataFrame or path to CSV file
            config: Configuration dict or path to JSON config file
        """
        self.data = self._load_data(data)
        self.config = self._load_config(config)
        self._validate_config()
    
    def _load_data(self, data: Union[pd.DataFrame, str, Path]) -> pd.DataFrame:
        """Load data from DataFrame or file path."""
        if isinstance(data, pd.DataFrame):
            return data.copy()
        elif isinstance(data, (str, Path)):
            path = Path(data)
            if not path.exists():
                raise FileError(f"Input file not found: {path}")
            try:
                return pd.read_csv(path)
            except Exception as e:
                raise FileError(f"Error reading CSV file: {e}")
        else:
            raise ValidationError("Data must be a DataFrame or file path")
    
    def _load_config(self, config: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """Load configuration from dict or JSON file."""
        if isinstance(config, dict):
            return config
        elif isinstance(config, (str, Path)):
            path = Path(config)
            if not path.exists():
                raise FileError(f"Configuration file not found: {path}")
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in config file: {e}")
        else:
            raise ValidationError("Config must be a dict or file path")
    
    def _validate_config(self) -> None:
        """Validate configuration structure."""
        if "Required" not in self.config:
            raise ConfigurationError("Configuration must contain 'Required' key")
        if not isinstance(self.config["Required"], list):
            raise ConfigurationError("'Required' must be a list of column names")
    
    def expand(self) -> pd.DataFrame:
        """
        Expand the data to include all required columns.
        
        Returns:
            DataFrame with all required columns populated
        """
        required_columns = self.config.get("Required", [])
        defaults = self.config.get("defaults", {})
        mapping = self.config.get("Mapping", {})
        
        # Create reverse mapping from input to output column names
        reverse_mapping = {v: k for k, v in mapping.items()}

        output_data = []
        for _, row in self.data.iterrows():
            output_row = {}
            for col in required_columns:
                # Prefer direct match, then mapped match, then default, else empty
                if col in self.data.columns:
                    output_row[col] = row[col]
                elif col in reverse_mapping and reverse_mapping[col] in row:
                    output_row[col] = row[reverse_mapping[col]]
                elif col in defaults:
                    output_row[col] = defaults[col]
                else:
                    output_row[col] = ""
            output_data.append(output_row)

        return pd.DataFrame(output_data) 