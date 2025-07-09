import argparse
import pandas as pd
import json
import os

class ScheduleExpander:
    def __init__(self, input_csv, json_config):
        self.input_csv = input_csv
        self.json_config = json_config
        self.df = pd.read_csv(input_csv)
        with open(json_config, 'r') as f:
            self.config = json.load(f)
        self.required_columns = self.config.get("Required", [])
        self.defaults = self.config.get("defaults", {})
        self.mapping = self.config.get("Mapping", {})

    def expand_columns(self):
        # Create reverse mapping from input to output column names
        reverse_mapping = {v: k for k, v in self.mapping.items()}

        output_data = []
        for _, row in self.df.iterrows():
            output_row = {}
            for col in self.required_columns:
                # Prefer direct match, then mapped match, then default, else empty
                if col in self.df.columns:
                    output_row[col] = row[col]
                elif col in reverse_mapping and reverse_mapping[col] in row:
                    output_row[col] = row[reverse_mapping[col]]
                elif col in self.defaults:
                    output_row[col] = self.defaults[col]
                else:
                    output_row[col] = ""
            output_data.append(output_row)

        return pd.DataFrame(output_data)

def main():
    parser = argparse.ArgumentParser(description="Expand CSV to include required columns with optional defaults and mappings.")
    parser.add_argument("input_csv", help="Path to the cleaned input CSV file.")
    parser.add_argument("config_json", help="Path to the JSON config file containing 'Required', optional 'defaults', and optional 'Mapping'.")
    parser.add_argument("--output", "-o", help="Path to save the expanded CSV file.")
    args = parser.parse_args()

    expander = ScheduleExpander(args.input_csv, args.config_json)
    df = expander.expand_columns()

    if args.output:
        df.to_csv(args.output, index=False)
    else:
        print(df.to_string(index=False))

if __name__ == "__main__":
    main()
