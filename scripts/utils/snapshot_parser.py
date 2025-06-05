import bz2
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

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
        records = []
        open_func = bz2.open if file_path.suffix == ".bz2" else open

        try:
            with open_func(file_path, "rt", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("op") != "mcm":
                        continue

                    for mc in data.get("mc", []):
                        market_id = mc.get("id", "")
                        market_def = mc.get("marketDefinition", {})
                        if not market_def or market_def.get("marketType") != "MATCH_ODDS":
                            continue

                        market_time = market_def.get("marketTime")
                        market_name = market_def.get("name", "")
                        runners = market_def.get("runners", [])
                        if len(runners) != 2:
                            continue

                        r1, r2 = runners[0].get("name", ""), runners[1].get("name", "")
                        s1, s2 = runners[0].get("id"), runners[1].get("id")
                        pt = data.get("pt", None)

                        if self.mode == "metadata":
                            return [{
                                "market_id": market_id,
                                "market_time": market_time,
                                "market_name": market_name,
                                "runner_1": r1,
                                "runner_2": r2
                            }]

                        if self.mode == "full":
                            records.append({
                                "market_id": market_id,
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
                                "market_id": market_id,
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
                            ltp = rc.get("ltp", None)
                            row = {
                                "market_id": market_id,
                                "selection_id": sel_id,
                                "ltp": ltp,
                                "timestamp": pt,
                                "market_time": market_time,
                                "market_name": market_name,
                                "runner_1": r1,
                                "runner_2": r2,
                            }
                            if self.mode == "full":
                                row["runner_name"] = next((r.get("name") for r in runners if r.get("id") == sel_id), None)
                            records.append(row)

                        if self.mode == "ltp_only":
                            break
        except Exception as e:
            print(f"❌ Failed: {file_path} — {e}")
        return records
