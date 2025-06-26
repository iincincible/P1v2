import subprocess
import sys
import json

SCRIPT = "src/scripts/builders/build_clean_matches_generic.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True
    )


def test_dry_run(tmp_path):
    out = tmp_path / "out.csv"
    r = run_cli(
        "--tour",
        "atp",
        "--tournament",
        "ausopen",
        "--year",
        "2023",
        "--output_csv",
        str(out),
        "--dry-run",
        "--verbose",
    )
    assert r.returncode == 0
    assert not out.exists()
    assert "Dry run" in r.stdout


def test_validation_error(tmp_path):
    # Create a CSV that lacks required columns
    bad = tmp_path / "bad.csv"
    bad.write_text("foo,bar\n1,2\n")
    r = run_cli(
        "--tour",
        "atp",
        "--tournament",
        "ausopen",
        "--year",
        "2023",
        "--snapshots",
        str(bad),
        "--output_csv",
        str(tmp_path / "out.csv"),
    )
    assert r.returncode == 2
    assert "Validation error" in r.stderr


def test_json_logs_and_overwrite(tmp_path):
    out = tmp_path / "matches.csv"
    # First run to create the file
    r1 = run_cli(
        "--tour",
        "atp",
        "--tournament",
        "ausopen",
        "--year",
        "2023",
        "--output_csv",
        str(out),
        "--overwrite",
    )
    assert r1.returncode == 0
    assert out.exists()

    # Run again with JSON logging
    r2 = run_cli(
        "--tour",
        "atp",
        "--tournament",
        "ausopen",
        "--year",
        "2023",
        "--output_csv",
        str(out),
        "--overwrite",
        "--json-logs",
    )
    first_line = r2.stdout.splitlines()[0]
    obj = json.loads(first_line)
    assert obj.get("levelname") == "INFO"
    assert r2.returncode == 0
