from pathlib import Path


def get_project_root() -> str:
    """
    Returns the root path
    """
    return str(Path(__file__).parent.parent.parent)