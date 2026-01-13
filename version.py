"""Version tracking for AI Calendar Agent"""
import subprocess
from datetime import datetime

# Manual version - bump this for releases
__version__ = "1.1.0"

def get_git_version():
    """Get version info from git (commit hash + dirty status)"""
    try:
        # Get short commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        # Check if working directory is dirty
        dirty = subprocess.call(
            ['git', 'diff', '--quiet'],
            stderr=subprocess.DEVNULL
        ) != 0

        return f"{commit}{'-dirty' if dirty else ''}"
    except Exception:
        return "unknown"

def get_full_version():
    """Get full version string: version + git commit"""
    return f"{__version__}+{get_git_version()}"

# Build info
BUILD_DATE = datetime.now().strftime("%Y-%m-%d %H:%M")
VERSION = __version__
VERSION_FULL = get_full_version()
