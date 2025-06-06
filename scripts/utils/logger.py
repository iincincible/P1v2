from datetime import datetime

def _timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def log_info(msg: str):
    print(f"{_timestamp()} ℹ️ {msg}")

def log_success(msg: str):
    print(f"{_timestamp()} ✅ {msg}")

def log_warning(msg: str):
    print(f"{_timestamp()} ⚠️ {msg}")

def log_error(msg: str):
    print(f"{_timestamp()} ❌ {msg}")
