import pandas as pd
import json
import warnings
import re
import argparse
import os

class ScheduleParser:
    DEFAULT_CONFIG = {
        "Format": {
            "Date": "%m/%d/%Y",
            "Time": "%I:%M %p",
            "Duration": "H:MM"
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

    def __init__(self, schedule_path, config_path=None, reference_date="2025-09-02"):
        self.schedule_path = schedule_path
        self.reference_date = pd.to_datetime(reference_date)

        if config_path:
            with open(config_path, "r") as f:
                self.config = json.load(f)
        else:
            fallback_path = os.path.join(os.path.dirname(schedule_path), "parser_config.json")
            if os.path.exists(fallback_path):
                with open(fallback_path, "r") as f:
                    self.config = json.load(f)
            else:
                self.config = self.DEFAULT_CONFIG

        self.df = pd.read_csv(self.schedule_path, sep="\t", header=None)

    def _parse_time_and_duration(self, interval):
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

    def _parse_block(self, block):
        date_col = block.columns[0]
        dates = block[date_col].iloc[3:].reset_index(drop=True)
        rows = []

        for col in block.columns[1:]:
            time_interval = block.iloc[2, block.columns.get_loc(col)]
            if pd.isna(time_interval):
                continue

            start_time, duration = self._parse_time_and_duration(time_interval)
            if not (start_time and duration):
                continue

            for i, team_entry in enumerate(block[col].iloc[3:].reset_index(drop=True)):
                date_str = dates.iloc[i]
                if pd.isna(date_str) or "ice" in str(date_str).lower():
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

    def parse_schedule(self):
        df = self.df
        date_cols = [col_idx for col_idx, val in enumerate(df.iloc[1]) if isinstance(val, str) and val.strip().lower() == "date"]

        blocks = []
        for i, date_col in enumerate(date_cols):
            cols = list(range(date_col, date_cols[i+1])) if i < len(date_cols)-1 else list(range(date_col, df.shape[1]))
            subset = df.iloc[:, cols].copy()
            mask = pd.Series(True, index=subset.index)
            mask[3:] = pd.notna(subset.iloc[3:, 0])
            subset = subset[mask]
            blocks.append(subset)

        dfs = [self._parse_block(block) for block in blocks if not self._parse_block(block).empty]

        if not dfs:
            return pd.DataFrame()

        result = pd.concat(dfs, ignore_index=True)
        result["Date"] = pd.to_datetime(result["Date"], format=self.config["Format"]["Date"])
        result = result.sort_values(["Date", "Start Time"]).reset_index(drop=True)
        result["Date"] = result["Date"].dt.strftime(self.config["Format"]["Date"])
        result.index.name = "Index"
        result.reset_index(inplace=True)
        return result

def main():
    parser = argparse.ArgumentParser(description="Parse hockey schedule from a structured tab-delimited file.")
    parser.add_argument("schedule", help="Path to the schedule input file (tab-delimited).")
    parser.add_argument("-c", "--config", help="Path to the config JSON file. Optional.", default=None)
    parser.add_argument("-o", "--output", help="Path to save output CSV. Optional.", default=None)
    parser.add_argument("--reference-date", help="Reference date for week calculation (default: 2025-09-02).", default="2025-09-02")
    args = parser.parse_args()

    sp = ScheduleParser(args.schedule, args.config, reference_date=args.reference_date)
    df = sp.parse_schedule()

    if args.output:
        df.to_csv(args.output, index=False)
    else:
        print(df)

if __name__ == "__main__":
    main()
