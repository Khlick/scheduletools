import click
from .parser import ScheduleParser
from .splitter import CSVSplitter
from .expander import ScheduleExpander

@click.group()
def main():
    """Schedule Tools CLI: Parse, split, and expand schedule data."""
    pass

@main.command()
@click.argument("schedule")
@click.option("--config", "-c", help="Path to config JSON.")
@click.option("--output", "-o", help="Output CSV path.")
@click.option("--reference-date", default="2025-09-02", help="Reference date (default: 2025-09-02)")
def parse(schedule, config, output, reference_date):
    """Parse a schedule file into structured CSV format."""
    sp = ScheduleParser(schedule, config, reference_date)
    df = sp.parse_schedule()
    if output:
        df.to_csv(output, index=False)
    else:
        click.echo(df.to_string(index=False))

@main.command()
@click.argument("input_csv")
@click.option("--groupby", "-g", required=True, help="Comma-separated columns to group by.")
@click.option("--filter", "-f", help="Include only entries with these values (comma-separated).")
@click.option("--exclude", "-x", help="Exclude entries with these values (comma-separated).")
@click.option("--output-dir", "-o", help="Directory to save split files.")
def split(input_csv, groupby, filter, exclude, output_dir):
    """Split CSV file into multiple files by group."""
    splitter = CSVSplitter(input_csv, groupby, filter, exclude)
    paths = splitter.split_and_export(output_dir)
    for path in paths:
        click.echo(f"Created: {path}")

@main.command()
@click.argument("input_csv")
@click.option("--template", "-t", required=True, help="Path to JSON template file.")
@click.option("--output", "-o", required=True, help="Path to save the expanded CSV.")
def expand(input_csv, template, output):
    """Expand schedule CSV to required column format."""
    expander = ScheduleExpander(input_csv, template)
    df = expander.expand()
    df.to_csv(output, index=False)
    click.echo(f"Expanded schedule saved to: {output}")
