"""
Command-line interface for ScheduleTools package.

This module provides CLI commands that use the core classes to perform
file-based operations (reading from files, writing to files).
"""

import click
import pandas as pd
from pathlib import Path
from typing import Optional

from .core import ScheduleParser, CSVSplitter, ScheduleExpander
from .exceptions import ScheduleToolsError


def handle_errors(func):
    """Decorator to handle exceptions and provide user-friendly error messages."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ScheduleToolsError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            raise click.Abort()
    return wrapper


@click.group()
@click.version_option()
def main():
    """ScheduleTools CLI: Professional spreadsheet wrangling utilities.
    
    Parse, split, and expand schedule data with configurable options.
    """
    pass


@main.command()
@click.argument("schedule", type=click.Path(exists=True, path_type=Path))
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), 
              help="Path to config JSON file.")
@click.option("--output", "-o", type=click.Path(path_type=Path), 
              help="Output CSV path. If not specified, prints to stdout.")
@click.option("--reference-date", default="2025-09-02", 
              help="Reference date for week calculations (default: 2025-09-02)")
@click.option("--block-marker", default="Date",
              help="Text marker that indicates the start of a block column (default: Date)")
@handle_errors
def parse(schedule: Path, config: Optional[Path], output: Optional[Path], 
          reference_date: str, block_marker: str):
    """Parse a schedule file into structured CSV format.
    
    SCHEDULE: Path to the input schedule file (tab-delimited format)
    """
    parser = ScheduleParser(schedule, config, reference_date, block_marker)
    df = parser.parse()
    
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
        click.echo(f"Parsed schedule saved to: {output}")
    else:
        click.echo(df.to_string(index=False))


@main.command()
@click.argument("input_csv", type=click.Path(exists=True, path_type=Path))
@click.option("--groupby", "-g", required=True, 
              help="Comma-separated columns to group by (e.g., 'Team' or 'Week,Team').")
@click.option("--filter", "-f", 
              help="Include only entries with these values (comma-separated).")
@click.option("--exclude", "-x", 
              help="Exclude entries with these values (comma-separated).")
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), 
              help="Directory to save split files (defaults to input file directory).")
@handle_errors
def split(input_csv: Path, groupby: str, filter: Optional[str], 
          exclude: Optional[str], output_dir: Optional[Path]):
    """Split CSV file into multiple files by group.
    
    INPUT_CSV: Path to the input CSV file to split
    """
    splitter = CSVSplitter(input_csv, groupby, filter, exclude)
    split_data = splitter.split()
    
    if not split_data:
        click.echo("No data to split. Check your filters or grouping criteria.")
        return
    
    # Determine output directory
    if output_dir is None:
        output_dir = input_csv.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each group to a separate file
    created_files = []
    for group_key, group_df in split_data.items():
        base_name = input_csv.stem
        output_filename = f"{base_name}_{group_key}.csv"
        output_path = output_dir / output_filename
        
        group_df.to_csv(output_path, index=False)
        created_files.append(output_path)
    
    click.echo(f"Created {len(created_files)} files in {output_dir}:")
    for file_path in created_files:
        click.echo(f"  {file_path.name}")


@main.command()
@click.argument("input_csv", type=click.Path(exists=True, path_type=Path))
@click.argument("template", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True,
              help="Path to save the expanded CSV.")
@handle_errors
def expand(input_csv: Path, template: Path, output: Path):
    """Expand schedule CSV to required column format.
    
    INPUT_CSV: Path to the input CSV file
    TEMPLATE: Path to JSON template file defining required columns and mappings
    """
    expander = ScheduleExpander(input_csv, template)
    df = expander.expand()
    
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    click.echo(f"Expanded schedule saved to: {output}")


@main.command()
@click.argument("input_csv", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path),
              help="Output directory for split files (defaults to input directory).")
@click.option("--template", "-t", type=click.Path(exists=True, path_type=Path),
              help="Template file for expansion (optional).")
@handle_errors
def process(input_csv: Path, output: Optional[Path], template: Optional[Path]):
    """Complete workflow: split and optionally expand CSV data.
    
    INPUT_CSV: Path to the input CSV file to process
    """
    # This is a convenience command that combines split and expand
    # For now, it just splits by common columns
    click.echo("Processing CSV file...")
    
    # Read the CSV to determine available columns
    df = pd.read_csv(input_csv)
    available_columns = list(df.columns)
    
    click.echo(f"Available columns: {', '.join(available_columns)}")
    
    # For now, just split by the first column if it looks like a grouping column
    if available_columns:
        group_col = available_columns[0]
        click.echo(f"Auto-selected grouping column: {group_col}")
        
        splitter = CSVSplitter(input_csv, group_col)
        split_data = splitter.split()
        
        if output is None:
            output = input_csv.parent
        
        output.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        for group_key, group_df in split_data.items():
            base_name = input_csv.stem
            output_filename = f"{base_name}_{group_key}.csv"
            output_path = output / output_filename
            
            # Apply expansion if template is provided
            if template:
                expander = ScheduleExpander(group_df, template)
                group_df = expander.expand()
            
            group_df.to_csv(output_path, index=False)
            created_files.append(output_path)
        
        click.echo(f"Created {len(created_files)} files in {output}:")
        for file_path in created_files:
            click.echo(f"  {file_path.name}")
    else:
        click.echo("No columns found in CSV file.")


if __name__ == "__main__":
    main()
