from datetime import datetime

def _timestamp():
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

def log_info(msg: str):
    print(f"{_timestamp()} INFO  {msg}")

def log_success(msg: str):
    print(f"{_timestamp()} OK ✅  {msg}")

def log_warning(msg: str):
    print(f"{_timestamp()} WARN ⚠️ {msg}")

def log_error(msg: str):
    print(f"{_timestamp()} ERR ❌  {msg}")
