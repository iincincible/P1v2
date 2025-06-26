import bz2
import json
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

from scripts.utils.logger import getLogger

logger = getLogger(__name__)


class SnapshotParser:
    """
    Parses Betfair snapshot files in various modes.

    Modes:
        - metadata: extract market metadata only
        - ltp_only: extract last traded prices only
        - full: extract both initial runner entries and LTP updates
    """

    VALID_MODES = {"metadata", "ltp_only", "full"}

    def __init__(self, mode: str = "full"):
        if mode not in self.VALID_MODES:
            raise ValueError(f"Unknown mode '{mode}'. Valid modes: {self.VALID_MODES}")
        self.mode = mode

    def should_parse_file(
        self, file_path: Path, start_date: datetime, end_date: datetime
    ) -> bool:
        """
        Determine if a snapshot file falls within the given date range
        based on its path parts (year-month-day).
        """
        try:
            parts = file_path.parts
            year, month, day = parts[-5], parts[-4], parts[-3]
            dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%b-%d")
            return start_date <= dt <= end_date
        except Exception as e:
            logger.debug("Skipping file %s: could not parse date (%s)", file_path, e)
            return False

    def parse_directory(
        self, input_dir: str | Path, start: datetime, end: datetime
    ) -> list[dict]:
        """
        Parse all .bz2 snapshot files within a directory and date range.
        """
        input_path = Path(input_dir)
        files = list(input_path.rglob("*.bz2"))
        filtered = [f for f in files if self.should_parse_file(f, start, end)]
        rows: list[dict] = []
        for f in tqdm(filtered, desc="Parsing snapshots", unit="file"):
            try:
                rows.extend(self.parse_file(f))
            except Exception as e:
                logger.error("Error parsing %s: %s", f, e)
        logger.info("Total records parsed: %d", len(rows))
        return rows

    def parse_file(self, file_path: Path) -> list[dict]:
        """
        Parse a single snapshot file based on the configured mode.
        """
        if self.mode == "metadata":
            return self._parse_metadata(file_path)
        if self.mode == "ltp_only":
            return self._parse_ltp_only(file_path)
        return self._parse_full(file_path)

    def _iter_records(self, file_path: Path):
        """
        Yield JSON objects from each line, skipping malformed lines.
        """
        open_fn = bz2.open if file_path.suffix == ".bz2" else open
        with open_fn(file_path, "rt", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(
                        "Malformed JSON in %s at line %d: %s", file_path, line_no, e
                    )

    def _filter_market(self, data: dict) -> bool:
        return data.get("op") == "mcm"

    def _parse_metadata(self, file_path: Path) -> list[dict]:
        records: list[dict] = []
        for data in self._iter_records(file_path):
            if not self._filter_market(data):
                continue
            for mc in data.get("mc", []):
                md = mc.get("marketDefinition", {})
                if md.get("marketType") != "MATCH_ODDS":
                    continue
                runners = md.get("runners", [])
                records.append(
                    {
                        "market_id": mc.get("id", ""),
                        "market_time": md.get("marketTime", ""),
                        "market_name": md.get("name", ""),
                        "runner_1": runners[0]["name"] if len(runners) >= 1 else "",
                        "runner_2": runners[1]["name"] if len(runners) >= 2 else "",
                    }
                )
        return records

    def _parse_ltp_only(self, file_path: Path) -> list[dict]:
        records: list[dict] = []
        for data in self._iter_records(file_path):
            if not self._filter_market(data):
                continue
            pt = data.get("pt")
            for mc in data.get("mc", []):
                mid = mc.get("id", "")
                for rc in mc.get("rc", []):
                    records.append(
                        {
                            "market_id": mid,
                            "selection_id": rc.get("id", ""),
                            "ltp": rc.get("ltp"),
                            "timestamp": pt,
                        }
                    )
        return records

    def _parse_full(self, file_path: Path) -> list[dict]:
        records: list[dict] = []
        for data in self._iter_records(file_path):
            if not self._filter_market(data):
                continue
            pt = data.get("pt")
            for mc in data.get("mc", []):
                md = mc.get("marketDefinition", {})
                if md.get("marketType") != "MATCH_ODDS":
                    continue
                runners = md.get("runners", [])
                if len(runners) != 2:
                    continue
                mt_str = md.get("marketTime", "")
                try:
                    mt_dt = datetime.fromisoformat(mt_str)
                    mt_ts = int(mt_dt.timestamp() * 1000)
                except Exception:
                    mt_ts = float("inf")
                r1, r2 = runners[0]["name"], runners[1]["name"]
                s1, s2 = runners[0]["id"], runners[1]["id"]
                # initial entries
                if pt <= mt_ts:
                    for runner_name, sel_id in [(r1, s1), (r2, s2)]:
                        records.append(
                            {
                                "market_id": mc.get("id", ""),
                                "selection_id": sel_id,
                                "ltp": None,
                                "timestamp": pt,
                                "market_time": mt_str,
                                "market_name": md.get("name", ""),
                                "runner_name": runner_name,
                                "runner_1": r1,
                                "runner_2": r2,
                            }
                        )
                # LTP updates
                for rc in mc.get("rc", []):
                    sel_id = rc.get("id")
                    if pt > mt_ts:
                        continue
                    ltp = rc.get("ltp")
                    name = next((r["name"] for r in runners if r["id"] == sel_id), "")
                    records.append(
                        {
                            "market_id": mc.get("id", ""),
                            "selection_id": sel_id,
                            "ltp": ltp,
                            "timestamp": pt,
                            "market_time": mt_str,
                            "market_name": md.get("name", ""),
                            "runner_name": name,
                            "runner_1": r1,
                            "runner_2": r2,
                        }
                    )
        return records
