import bz2
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm  # ✅ Progress bar added
from scripts.utils.logger import log_error


class SnapshotParser:
    def __init__(self, mode="full"):
        self.mode = mode

    def should_parse_file(self, file_path, start_date, end_date):
        try:
            parts = file_path.parts
            year, month, day = parts[-5], parts[-4], parts[-3]
            dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%b-%d")
            return start_date <= dt <= end_date
        except Exception:
            return False

    def parse_file(self, file_path):
        try:
            if self.mode == "metadata":
                return self._parse_metadata(file_path)
            elif self.mode == "ltp_only":
                return self._parse_ltp_only(file_path)
            else:
                return self._parse_full(file_path)
        except Exception as e:
            log_error(f"❌ Failed: {file_path} — {e}")
            return []

    def _read_lines(self, file_path):
        open_func = bz2.open if file_path.suffix == ".bz2" else open
        with open_func(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)

    def _parse_metadata(self, file_path):
        for data in self._read_lines(file_path):
            if data.get("op") != "mcm":
                continue
            for mc in data.get("mc", []):
                md = mc.get("marketDefinition", {})
                if md.get("marketType") != "MATCH_ODDS":
                    continue
                return [{
                    "market_id": mc.get("id", ""),
                    "market_time": md.get("marketTime"),
                    "market_name": md.get("name", ""),
                    "runner_1": md["runners"][0]["name"] if len(md.get("runners", [])) >= 2 else "",
                    "runner_2": md["runners"][1]["name"] if len(md.get("runners", [])) >= 2 else "",
                }]
        return []

    def _parse_ltp_only(self, file_path):
        records = []
        for data in self._read_lines(file_path):
            if data.get("op") != "mcm":
                continue
            pt = data.get("pt")
            for mc in data.get("mc", []):
                mid = mc.get("id")
                for rc in mc.get("rc", []):
                    records.append({
                        "market_id": mid,
                        "selection_id": rc.get("id"),
                        "ltp": rc.get("ltp"),
                        "timestamp": pt
                    })
        return records

    def _parse_full(self, file_path):
        records = []
        for data in self._read_lines(file_path):
            if data.get("op") != "mcm":
                continue
            pt = data.get("pt")
            for mc in data.get("mc", []):
                mid = mc.get("id")
                md = mc.get("marketDefinition", {})
                if md.get("marketType") != "MATCH_ODDS":
                    continue
                runners = md.get("runners", [])
                if len(runners) != 2:
                    continue

                r1, r2 = runners[0]["name"], runners[1]["name"]
                s1, s2 = runners[0]["id"], runners[1]["id"]
                market_time = md.get("marketTime")
                market_name = md.get("name", "")

                records.append({
                    "market_id": mid,
                    "selection_id": s1,
                    "ltp": None,
                    "timestamp": pt,
                    "market_time": market_time,
                    "market_name": market_name,
                    "runner_name": r1,
                    "runner_1": r1,
                    "runner_2": r2
                })
                records.append({
                    "market_id": mid,
                    "selection_id": s2,
                    "ltp": None,
                    "timestamp": pt,
                    "market_time": market_time,
                    "market_name": market_name,
                    "runner_name": r2,
                    "runner_1": r1,
                    "runner_2": r2
                })

                for rc in mc.get("rc", []):
                    sel_id = rc.get("id")
                    ltp = rc.get("ltp")
                    name = next((r["name"] for r in runners if r["id"] == sel_id), None)
                    records.append({
                        "market_id": mid,
                        "selection_id": sel_id,
                        "ltp": ltp,
                        "timestamp": pt,
                        "market_time": market_time,
                        "market_name": market_name,
                        "runner_name": name,
                        "runner_1": r1,
                        "runner_2": r2
                    })
        return records

    def parse_directory(self, input_dir: str, start: datetime, end: datetime) -> list[dict]:
        """
        Parses all snapshot files in a directory within the given date range, with progress bar.
        """
        input_path = Path(input_dir)
        all_files = list(input_path.rglob("*.bz2"))
        filtered = [f for f in all_files if self.should_parse_file(f, start, end)]
        rows = []
        for f in tqdm(filtered, desc="Parsing snapshots", unit="file"):
            rows.extend(self.parse_file(f))
        return rows
