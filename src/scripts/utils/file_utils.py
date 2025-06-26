from pathlib import Path


def ensure_writable_path(path, overwrite=False):
    p = Path(path)
    if p.exists() and not overwrite:
        raise FileExistsError(f"{p} exists and overwrite is False.")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
