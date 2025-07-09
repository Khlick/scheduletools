#!/usr/bin/env python3
"""
Basic usage example for ScheduleTools library.

This example demonstrates how to use the core classes programmatically
to parse, split, and expand schedule data.
"""

import pandas as pd
from pathlib import Path

from scheduletools import ScheduleParser, CSVSplitter, ScheduleExpander


def main():
    """Demonstrate basic usage of ScheduleTools."""
    
    # Example 1: Parse schedule data
    print("=== Example 1: Parsing Schedule Data ===")
    
    # Create sample data (in real usage, this would be a file)
    sample_data = pd.DataFrame({
        'Date': ['09/02/2025', '09/03/2025', '09/04/2025'],
        'Start Time': ['7:00 PM', '8:30 PM', '6:00 PM'],
        'Duration': ['1:30', '1:30', '1:30'],
        'Team': ['Team A', 'Team B', 'Team A'],
        'Week': [0, 0, 0],
        'Day': ['Monday', 'Tuesday', 'Wednesday']
    })
    
    # Save sample data to CSV for demonstration
    sample_file = Path("sample_schedule.csv")
    sample_data.to_csv(sample_file, index=False)
    
    try:
        # Parse the schedule (in real usage, this would parse from a specific format)
        print(f"Sample data created: {sample_file}")
        print(sample_data.head())
        
    except Exception as e:
        print(f"Error parsing schedule: {e}")
    
    # Example 2: Split data by team
    print("\n=== Example 2: Splitting Data by Team ===")
    
    try:
        splitter = CSVSplitter(sample_data, "Team")
        team_schedules = splitter.split()
        
        print(f"Split data into {len(team_schedules)} groups:")
        for team, team_df in team_schedules.items():
            print(f"  {team}: {len(team_df)} entries")
            print(f"    Sample: {team_df[['Date', 'Start Time', 'Team']].head(2).to_string()}")
            
    except Exception as e:
        print(f"Error splitting data: {e}")
    
    # Example 3: Expand data with required columns
    print("\n=== Example 3: Expanding Data with Required Columns ===")
    
    # Define expansion configuration
    expansion_config = {
        "Required": ["Date", "Time", "Team", "Location", "Notes", "Status"],
        "defaults": {
            "Location": "Main Arena",
            "Notes": "",
            "Status": "Scheduled"
        },
        "Mapping": {
            "Start Time": "Time"
        }
    }
    
    try:
        expander = ScheduleExpander(sample_data, expansion_config)
        expanded_data = expander.expand()
        
        print("Expanded data with required columns:")
        print(expanded_data.to_string(index=False))
        
    except Exception as e:
        print(f"Error expanding data: {e}")
    
    # Example 4: Complete workflow
    print("\n=== Example 4: Complete Workflow ===")
    
    try:
        # 1. Split by team
        splitter = CSVSplitter(sample_data, "Team")
        team_schedules = splitter.split()
        
        # 2. Expand each team's schedule
        expanded_teams = {}
        for team_name, team_df in team_schedules.items():
            expander = ScheduleExpander(team_df, expansion_config)
            expanded_teams[team_name] = expander.expand()
        
        # 3. Show results
        print("Complete workflow results:")
        for team_name, expanded_df in expanded_teams.items():
            print(f"\n{team_name} Schedule:")
            print(expanded_df.to_string(index=False))
            
    except Exception as e:
        print(f"Error in complete workflow: {e}")
    
    # Cleanup
    if sample_file.exists():
        sample_file.unlink()
        print(f"\nCleaned up: {sample_file}")


if __name__ == "__main__":
    main() 