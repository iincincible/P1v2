import argparse
import yaml
import subprocess
from pathlib import Path
import os
import sys

from scripts.utils.logger import log_info, log_success, log_warning
from scripts.utils.cli_utils import add_common_flags, merge_with_defaults, should_run


PYTHON = sys.executable
DEFAULT_CONFIG = "configs/pipeline_run.yaml"


def main():
    parser = argparse.ArgumentParser(description="Run full value betting pipeline.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to pipeline YAML config")
    parser.add_argument("--only", nargs="*", help="Optional list of stages to run (e.g., 'predict detect simulate')")
    add_common_flags(parser)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    stages = config.get("stages", [])
    defaults = config.get("defaults", {})

    for stage in stages:
        conf = merge_with_defaults(stage, defaults)
        label = conf.get("label") or stage.get("label", "unknown")
        script = conf["script"]
        output = conf.get("output")

        if args.only and conf.get("name") not in args.only:
            continue

        output_path = Path(output) if output else None
        if output_path and not should_run(output_path, args.overwrite, args.dry_run):
            continue

        cmd = [PYTHON, script]
        for k, v in conf.items():
            if k in {"script", "name", "label"}:
                continue
            if isinstance(v, bool):
                if v:
                    cmd.append(f"--{k}")
            else:
                cmd += [f"--{k}", str(v)]
        if args.overwrite:
            cmd.append("--overwrite")
        if args.dry_run:
            log_info(f"🧪 Dry run: would run {script}")
            log_info("      " + " ".join(cmd))
            continue

        log_info(f"\n🚀 Running: {label}")
        log_info("      " + " ".join(cmd))
        subprocess.run(cmd, check=True, env={**os.environ, "PYTHONPATH": "."})
        if output:
            log_success(f"✅ Completed: {label} → {output}")


if __name__ == "__main__":
    main()
