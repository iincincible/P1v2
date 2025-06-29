import bz2
import json
from pathlib import Path
from typing import List, Dict, Any


class SnapshotParser:
    """
    Parses Betfair snapshot files (plain text or .bz2) containing JSON lines.

    Modes:
      - "metadata": extracts marketDefinition metadata into a list of dicts
      - "ltp_only": extracts last-traded-price updates for each runner
      - "full": extracts all available runner-change fields
    """

    VALID_MODES = {"metadata", "ltp_only", "full"}

    def __init__(self, mode: str = "full"):
        if mode not in self.VALID_MODES:
            raise ValueError(
                f"Unknown mode: {mode!r}. Valid modes are: {self.VALID_MODES}"
            )
        self.mode = mode

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read the given file (plain text or .bz2) line by line, parse each JSON
        message, and return a list of row-dicts according to the selected mode.

        :param file_path: path to a .txt/.csv or .bz2 snapshot file
        :return: list of dicts containing the requested data for each mode
        """
        # Wrap in Path so we can branch on suffix
        p = Path(file_path)
        opener = bz2.open if p.suffix == ".bz2" else open

        rows: List[Dict[str, Any]] = []
        with opener(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip malformed lines

                # We only care about market-change messages
                if msg.get("op") != "mcm":
                    continue

                for change in msg.get("mc", []):
                    market_id = change.get("id")
                    publish_time = msg.get("pt")

                    if self.mode == "metadata":
                        md = change.get("marketDefinition", {})
                        row: Dict[str, Any] = {
                            "market_id": market_id,
                            "market_time": md.get("marketTime"),
                            "market_name": md.get("name"),
                        }
                        # dynamically pull runner_1, runner_2, …
                        for idx, runner in enumerate(md.get("runners", []), start=1):
                            row[f"runner_{idx}"] = runner.get("name")
                        rows.append(row)

                    elif self.mode == "ltp_only":
                        for rc in change.get("rc", []):
                            if "ltp" in rc:
                                rows.append(
                                    {
                                        "market_id": market_id,
                                        "market_time": publish_time,
                                        "runner_id": rc.get("id"),
                                        "last_traded_price": rc.get("ltp"),
                                    }
                                )

                    else:  # self.mode == "full"
                        for rc in change.get("rc", []):
                            row: Dict[str, Any] = {
                                "market_id": market_id,
                                "market_time": publish_time,
                                "runner_id": rc.get("id"),
                            }
                            if "ltp" in rc:
                                row["last_traded_price"] = rc["ltp"]
                            if "tv" in rc:
                                row["total_matched"] = rc["tv"]
                            if "atb" in rc:
                                row["best_available_to_back"] = rc["atb"]
                            if "atl" in rc:
                                row["best_available_to_lay"] = rc["atl"]
                            rows.append(row)

        return rows
