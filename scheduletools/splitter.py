import argparse
import pandas as pd
import os
import re

class CSVSplitter:
    def __init__(self, input_file, group_columns, include_values=None, exclude_values=None):
        self.input_file = input_file
        self.group_columns = [col.strip() for col in group_columns.split(",")]
        self.df = pd.read_csv(input_file)
        self.include_values = [v.strip() for v in include_values.split(",")] if include_values else None
        self.exclude_values = [v.strip() for v in exclude_values.split(",")] if exclude_values else None

    def _sanitize_filename(self, name):
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def _should_include(self, group_keys):
        keys = [str(k) for k in group_keys] if isinstance(group_keys, tuple) else [str(group_keys)]

        if self.include_values and not any(k in self.include_values for k in keys):
            return False
        if self.exclude_values and any(k in self.exclude_values for k in keys):
            return False
        return True

    def split_and_export(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(self.input_file))
        os.makedirs(output_dir, exist_ok=True)

        grouped = self.df.groupby(self.group_columns)
        file_paths = []

        for group_keys, group_df in grouped:
            if not self._should_include(group_keys):
                continue

            keys = group_keys if isinstance(group_keys, tuple) else (group_keys,)
            safe_keys = [self._sanitize_filename(str(k).replace(" ", "_")) for k in keys]
            suffix = "_".join(safe_keys)
            base_name = os.path.splitext(os.path.basename(self.input_file))[0]
            output_filename = f"{base_name}_{suffix}.csv"
            output_path = os.path.join(output_dir, output_filename)

            group_df.to_csv(output_path, index=False)
            file_paths.append(output_path)

        return file_paths

def main():
    parser = argparse.ArgumentParser(description="Split a CSV into multiple files by grouping and optionally filtering.")
    parser.add_argument("input_csv", help="Path to input CSV file.")
    parser.add_argument("--groupby", "-g", required=True, help="Comma-separated columns to group by (e.g. 'Team' or 'Week,Team').")
    parser.add_argument("--output-dir", "-o", help="Output directory (defaults to input file's directory).")
    parser.add_argument("--filter", "-f", help="Comma-separated values to include (optional).")
    parser.add_argument("--exclude", "-x", help="Comma-separated values to exclude (optional).")

    args = parser.parse_args()

    splitter = CSVSplitter(
        input_file=args.input_csv,
        group_columns=args.groupby,
        include_values=args.filter,
        exclude_values=args.exclude
    )
    paths = splitter.split_and_export(args.output_dir)

    if paths:
        print("Created the following files:")
        for path in paths:
            print(path)
    else:
        print("No files created. (Check filters or grouping.)")

if __name__ == "__main__":
    main()
