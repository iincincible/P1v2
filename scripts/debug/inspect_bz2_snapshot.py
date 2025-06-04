import bz2
import json
import sys

# Replace this with your actual .bz2 file path or pass it as a CLI argument
BZ2_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/BASIC/2023/May/31/32382053/1.214856894.bz2"

print(f"🔍 Inspecting file: {BZ2_PATH}")

try:
    with bz2.open(BZ2_PATH, "rt") as f:
        for i, line in enumerate(f):
            if i >= 50:
                break
            try:
                data = json.loads(line)
                print(json.dumps(data, indent=2))  # Pretty-print
            except Exception as e:
                print(f"⚠️ Error parsing line {i}: {e}")
except FileNotFoundError:
    print(f"❌ File not found: {BZ2_PATH}")
except Exception as e:
    print(f"❌ Error opening file: {e}")
