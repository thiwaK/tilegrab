from pathlib import Path

def get_attr_by_path(obj, path):
    """Walk dotted attribute path (raises AttributeError if missing)."""
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj

def has_attr_path(obj, path):
    """Return True if the dotted attribute path exists on obj."""
    try:
        _ = get_attr_by_path(obj, path)
        return True
    except AttributeError:
        return False

def normalize_expected(expected):
    """Normalize expected values for comparison in tests (Path resolution)."""
    if isinstance(expected, (str, Path)) and str(expected).startswith((".", "/", "\\")):
        return Path(expected).resolve()
    return expected
