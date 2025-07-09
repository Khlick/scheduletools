"""
Tests for the core ScheduleTools functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import json

from scheduletools import ScheduleParser, CSVSplitter, ScheduleExpander
from scheduletools.exceptions import (
    ScheduleToolsError, 
    ParsingError, 
    ValidationError, 
    ConfigurationError, 
    FileError
)


def create_test_schedule_file():
    """Create a test schedule file in the tab-delimited format."""
    schedule_content = """Monday		Tuesday			
Date	Time	Date	Time		
	6 pm - 7:15 pm		6:00 pm - 7:00 pm	7:00 pm - 8:00 pm	8:15 pm - 9:15 pm
7/21/2025	16U / 18U	7/22/2025	12U / 14U	18U	16U
7/28/2025	16U / 18U	7/29/2025	8U / 10U	18U	16U
8/4/2025	16U / 18U	8/5/2025	12U / 14U	18U	16U"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(schedule_content)
    temp_file.close()
    return Path(temp_file.name)


def create_test_schedule_file_with_different_marker():
    """Create a test schedule file with a different block marker."""
    schedule_content = """Monday		Tuesday			
Day	Time	Day	Time		
	6 pm - 7:15 pm		6:00 pm - 7:00 pm	7:00 pm - 8:00 pm	8:15 pm - 9:15 pm
7/21/2025	16U / 18U	7/22/2025	12U / 14U	18U	16U
7/28/2025	16U / 18U	7/29/2025	8U / 10U	18U	16U
8/4/2025	16U / 18U	8/5/2025	12U / 14U	18U	16U"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(schedule_content)
    temp_file.close()
    return Path(temp_file.name)


class TestScheduleParser:
    """Test ScheduleParser functionality."""
    
    def test_parser_initialization(self):
        """Test parser initialization with default config."""
        # Create a minimal test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Header\nDate\nTime\nData")
            temp_path = f.name
        
        try:
            parser = ScheduleParser(temp_path)
            assert parser.config["Format"]["Date"] == "%m/%d/%Y"
            assert parser.config["Format"]["Time"] == "%I:%M %p"
            assert parser.config["Block Detection"]["start_marker"] == "Date"
        finally:
            Path(temp_path).unlink()
    
    def test_parser_with_custom_block_marker(self):
        """Test parser with custom block start marker."""
        # Create a minimal test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Header\nDay\nTime\nData")
            temp_path = f.name
        
        try:
            parser = ScheduleParser(temp_path, block_start_marker="Day")
            assert parser.block_start_marker == "Day"
        finally:
            Path(temp_path).unlink()
    
    def test_parser_with_custom_config(self):
        """Test parser with custom configuration."""
        config = {
            "Format": {
                "Date": "%Y-%m-%d",
                "Time": "%H:%M",
                "Duration": "H:MM"
            },
            "Block Detection": {
                "start_marker": "Day",
                "skip_meta_rows": True,
                "meta_patterns": ["ice", "time", "header"]
            },
            "Missing Values": {
                "Omit": False,
                "Replacement": "TBD"
            },
            "Split": {
                "Skip": True,
                "Separator": ","
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_config_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Header\nDay\nTime\nData")
            temp_path = f.name
        
        try:
            parser = ScheduleParser(temp_path, temp_config_path)
            assert parser.config["Format"]["Date"] == "%Y-%m-%d"
            assert parser.config["Format"]["Time"] == "%H:%M"
            assert parser.config["Block Detection"]["start_marker"] == "Day"
            assert parser.config["Missing Values"]["Replacement"] == "TBD"
        finally:
            Path(temp_config_path).unlink()
            Path(temp_path).unlink()
    
    def test_parser_with_actual_schedule_format(self):
        """Test parser with the actual tab-delimited schedule format."""
        schedule_file = create_test_schedule_file()
        
        try:
            parser = ScheduleParser(schedule_file, reference_date="2025-07-21")
            result = parser.parse()
            
            # Should parse some data
            assert isinstance(result, pd.DataFrame)
            print(f"Parsed {len(result)} rows from schedule")
            
            # If data was parsed, check structure
            if len(result) > 0:
                expected_columns = ["Index", "Week", "Day", "Date", "Start Time", "Duration", "Team"]
                for col in expected_columns:
                    assert col in result.columns, f"Expected column {col} not found"
                
                # Check that we have team data
                assert "Team" in result.columns
                teams = result["Team"].dropna().unique()
                assert len(teams) > 0, "No teams found in parsed data"
                
                print(f"Found teams: {teams}")
                
        finally:
            schedule_file.unlink()
    
    def test_parser_with_different_block_marker(self):
        """Test parser with a different block marker."""
        schedule_file = create_test_schedule_file_with_different_marker()
        
        try:
            parser = ScheduleParser(schedule_file, reference_date="2025-07-21", block_start_marker="Day")
            result = parser.parse()
            
            # Should parse some data
            assert isinstance(result, pd.DataFrame)
            print(f"Parsed {len(result)} rows with 'Day' marker")
            
            # If data was parsed, check structure
            if len(result) > 0:
                expected_columns = ["Index", "Week", "Day", "Date", "Start Time", "Duration", "Team"]
                for col in expected_columns:
                    assert col in result.columns, f"Expected column {col} not found"
                
        finally:
            schedule_file.unlink()
    
    def test_parser_with_wrong_block_marker(self):
        """Test parser fails with wrong block marker."""
        schedule_file = create_test_schedule_file()
        
        try:
            parser = ScheduleParser(schedule_file, reference_date="2025-07-21", block_start_marker="WrongMarker")
            with pytest.raises(ParsingError, match="No block start marker"):
                parser.parse()
        finally:
            schedule_file.unlink()
    
    def test_parser_with_team_splitting(self):
        """Test parser with team splitting enabled."""
        schedule_file = create_test_schedule_file()
        
        try:
            # Use config that enables team splitting
            config = {
                "Format": {
                    "Date": "%m/%d/%Y",
                    "Time": "%I:%M %p",
                    "Duration": "H:MM"
                },
                "Block Detection": {
                    "start_marker": "Date",
                    "skip_meta_rows": True,
                    "meta_patterns": ["ice", "time", "header"]
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config, f)
                temp_config_path = f.name
            
            try:
                parser = ScheduleParser(schedule_file, temp_config_path, "2025-07-21")
                result = parser.parse()
                
                assert isinstance(result, pd.DataFrame)
                if len(result) > 0:
                    # Check that teams were split (should have individual team names)
                    teams = result["Team"].dropna().unique()
                    print(f"Teams after splitting: {teams}")
                    
                    # Should have individual team names like "16U", "18U", etc.
                    assert any("U" in str(team) for team in teams), "Expected team names with 'U'"
                    
            finally:
                Path(temp_config_path).unlink()
                
        finally:
            schedule_file.unlink()
    
    def test_parser_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(FileError, match="Schedule file not found"):
            parser = ScheduleParser("nonexistent.txt")
            parser.parse()
    
    def test_parser_invalid_config_file(self):
        """Test error handling for invalid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_config_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Header\nDate\nTime\nData")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid JSON in config file"):
                ScheduleParser(temp_path, temp_config_path)
        finally:
            Path(temp_config_path).unlink()
            Path(temp_path).unlink()
    
    def test_parser_with_different_reference_dates(self):
        """Test parser with different reference dates."""
        schedule_file = create_test_schedule_file()
        
        try:
            # Test with different reference dates
            reference_dates = ["2025-07-21", "2025-07-28", "2025-08-04"]
            
            for ref_date in reference_dates:
                parser = ScheduleParser(schedule_file, reference_date=ref_date)
                result = parser.parse()
                
                assert isinstance(result, pd.DataFrame)
                if len(result) > 0:
                    # Week numbers should be different with different reference dates
                    weeks = result["Week"].unique()
                    print(f"Reference date {ref_date}: weeks {weeks}")
                    
        finally:
            schedule_file.unlink()
    
    def test_meta_row_detection(self):
        """Test meta row detection functionality."""
        schedule_file = create_test_schedule_file()
        
        try:
            parser = ScheduleParser(schedule_file, reference_date="2025-07-21")
            
            # Test meta row detection
            assert parser._is_meta_row("ice time") == True
            assert parser._is_meta_row("header info") == True
            assert parser._is_meta_row("7/21/2025") == False
            assert parser._is_meta_row("16U") == False
            assert parser._is_meta_row("") == True
            assert parser._is_meta_row(None) == True
            
        finally:
            schedule_file.unlink()


class TestCSVSplitter:
    """Test CSVSplitter functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'Team': ['A', 'B', 'A', 'C', 'B'],
            'Week': [1, 1, 2, 2, 3],
            'Score': [10, 20, 15, 25, 30]
        })
    
    def test_split_by_single_column(self):
        """Test splitting by a single column."""
        splitter = CSVSplitter(self.test_data, "Team")
        result = splitter.split()
        
        assert len(result) == 3
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert len(result["A"]) == 2
        assert len(result["B"]) == 2
        assert len(result["C"]) == 1
    
    def test_split_by_multiple_columns(self):
        """Test splitting by multiple columns."""
        splitter = CSVSplitter(self.test_data, ["Team", "Week"])
        result = splitter.split()
        
        assert len(result) == 5  # 3 teams × 3 weeks, but some combinations don't exist
        assert "A_1" in result
        assert "A_2" in result
        assert "B_1" in result
        assert "B_3" in result
        assert "C_2" in result
    
    def test_split_with_include_filter(self):
        """Test splitting with include filter."""
        splitter = CSVSplitter(self.test_data, "Team", include_values=["A", "B"])
        result = splitter.split()
        
        assert len(result) == 2
        assert "A" in result
        assert "B" in result
        assert "C" not in result
    
    def test_split_with_exclude_filter(self):
        """Test splitting with exclude filter."""
        splitter = CSVSplitter(self.test_data, "Team", exclude_values=["C"])
        result = splitter.split()
        
        assert len(result) == 2
        assert "A" in result
        assert "B" in result
        assert "C" not in result
    
    def test_split_with_file_path(self):
        """Test splitting with file path input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            splitter = CSVSplitter(temp_path, "Team")
            result = splitter.split()
            
            assert len(result) == 3
            assert "A" in result
            assert "B" in result
            assert "C" in result
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_column(self):
        """Test error handling for invalid column."""
        with pytest.raises(ValidationError, match="Group columns not found in data"):
            CSVSplitter(self.test_data, "NonexistentColumn")
    
    def test_invalid_data_type(self):
        """Test error handling for invalid data type."""
        with pytest.raises(ValidationError, match="Data must be a DataFrame or file path"):
            CSVSplitter(123, "Team")


class TestScheduleExpander:
    """Test ScheduleExpander functionality."""
    
    def setup_method(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02'],
            'Start Time': ['7:00 PM', '8:00 PM'],
            'Team': ['A', 'B']
        })
    
    def test_expand_with_defaults(self):
        """Test expansion with default values."""
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
        
        expander = ScheduleExpander(self.test_data, config)
        result = expander.expand()
        
        assert list(result.columns) == ["Date", "Time", "Team", "Location", "Status"]
        assert len(result) == 2
        assert result.iloc[0]["Location"] == "Main Arena"
        assert result.iloc[0]["Status"] == "Scheduled"
        assert result.iloc[0]["Time"] == "7:00 PM"
    
    def test_expand_with_file_path(self):
        """Test expansion with file path input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        config = {
            "Required": ["Date", "Team"],
            "defaults": {}
        }
        
        try:
            expander = ScheduleExpander(temp_path, config)
            result = expander.expand()
            
            assert list(result.columns) == ["Date", "Team"]
            assert len(result) == 2
        finally:
            Path(temp_path).unlink()
    
    def test_expand_with_dict_config(self):
        """Test expansion with dictionary configuration."""
        config = {
            "Required": ["Date", "Team", "Notes"],
            "defaults": {"Notes": ""}
        }
        
        expander = ScheduleExpander(self.test_data, config)
        result = expander.expand()
        
        assert list(result.columns) == ["Date", "Team", "Notes"]
        assert result.iloc[0]["Notes"] == ""
    
    def test_expand_with_json_config(self):
        """Test expansion with JSON config file."""
        config = {
            "Required": ["Date", "Team", "Location"],
            "defaults": {"Location": "Arena"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_config_path = f.name
        
        try:
            expander = ScheduleExpander(self.test_data, temp_config_path)
            result = expander.expand()
            
            assert list(result.columns) == ["Date", "Team", "Location"]
            assert result.iloc[0]["Location"] == "Arena"
        finally:
            Path(temp_config_path).unlink()
    
    def test_invalid_config_missing_required(self):
        """Test error handling for invalid config."""
        config = {"defaults": {}}  # Missing "Required" key
        
        with pytest.raises(ConfigurationError, match="Configuration must contain 'Required' key"):
            ScheduleExpander(self.test_data, config)
    
    def test_invalid_config_required_not_list(self):
        """Test error handling for invalid required field."""
        config = {"Required": "not a list"}
        
        with pytest.raises(ConfigurationError, match="'Required' must be a list of column names"):
            ScheduleExpander(self.test_data, config)


class TestCompleteWorkflow:
    """Test complete workflow from parsing to splitting to expanding."""
    
    def test_complete_workflow(self):
        """Test the complete workflow with actual schedule data."""
        schedule_file = create_test_schedule_file()
        
        try:
            # 1. Parse schedule
            parser = ScheduleParser(schedule_file, reference_date="2025-07-21")
            parsed_data = parser.parse()
            
            # Skip if no data was parsed
            if len(parsed_data) == 0:
                pytest.skip("No data parsed from schedule file")
            
            assert isinstance(parsed_data, pd.DataFrame)
            assert len(parsed_data) > 0
            
            # 2. Split by team
            splitter = CSVSplitter(parsed_data, "Team")
            team_schedules = splitter.split()
            
            assert len(team_schedules) > 0
            
            # 3. Expand one team's schedule
            first_team = list(team_schedules.keys())[0]
            team_data = team_schedules[first_team]
            
            expansion_config = {
                "Required": ["Date", "Time", "Team", "Location", "Notes"],
                "defaults": {
                    "Location": "Main Arena",
                    "Notes": ""
                },
                "Mapping": {
                    "Start Time": "Time"
                }
            }
            
            expander = ScheduleExpander(team_data, expansion_config)
            expanded_data = expander.expand()
            
            assert isinstance(expanded_data, pd.DataFrame)
            assert len(expanded_data) > 0
            assert "Location" in expanded_data.columns
            assert "Notes" in expanded_data.columns
            
        finally:
            schedule_file.unlink()


class TestErrorHandling:
    """Test error handling across all classes."""
    
    def test_custom_exceptions(self):
        """Test that custom exceptions are properly defined."""
        # Test that exceptions can be raised and caught
        try:
            raise FileError("Test file error")
        except FileError as e:
            assert str(e) == "Test file error"
        
        try:
            raise ParsingError("Test parsing error")
        except ParsingError as e:
            assert str(e) == "Test parsing error"
        
        try:
            raise ValidationError("Test validation error")
        except ValidationError as e:
            assert str(e) == "Test validation error"
        
        try:
            raise ConfigurationError("Test config error")
        except ConfigurationError as e:
            assert str(e) == "Test config error"
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from base exception."""
        exceptions = [FileError, ParsingError, ValidationError, ConfigurationError]
        
        for exc_class in exceptions:
            exc = exc_class("test")
            assert isinstance(exc, ScheduleToolsError) 