# scripts/monitor_extraction_progress.py

import time
from pathlib import Path

def count_bz2_files(folder: Path):
    return len(list(folder.rglob("*.bz2")))

def main():
    target_folder = Path.home() / "Projects" / "P1v2" / "data" / "BASIC"
    print(f"🔍 Monitoring .bz2 files in {target_folder}...")

    previous_count = -1
    try:
        while True:
            current_count = count_bz2_files(target_folder)
            if current_count != previous_count:
                print(f"🧾 {current_count:,} .bz2 files found", end="\r")
                previous_count = current_count
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n✅ Final count: {current_count:,} .bz2 files.")
        print("🛑 Monitoring stopped.")

if __name__ == "__main__":
    main()
