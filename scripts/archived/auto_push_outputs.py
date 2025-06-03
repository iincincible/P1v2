import subprocess
from datetime import datetime

def run_auto_push():
    timestamp = datetime.now().strftime("🔁 Auto-push: updated outputs @ %Y-%m-%d %H:%M")

    # Only stage output files (not scripts or core code)
    files_to_add = [
        "requirements.txt",
        "data/processed/",
        "data/plots/",
        "parsed/"
    ]

    try:
        # Stage selected files/folders
        for item in files_to_add:
            subprocess.run(["git", "add", item], check=True)

        # Commit with timestamped message
        subprocess.run(["git", "commit", "-m", timestamp], check=True)

        # Push to remote
        subprocess.run(["git", "push"], check=True)
        print("✅ Auto-push complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

if __name__ == "__main__":
    run_auto_push()
