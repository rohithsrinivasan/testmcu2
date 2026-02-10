# submodule/utils/path.py

import os

def get_submodule_root():
    """
    Returns the absolute path to the submodule's root directory.
    This works whether run from the submodule alone or as part of a parent project.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def submodule_path(*relative_parts):
    """
    Constructs a full path to a file/folder relative to the submodule root.
    Usage: submodule_path('database', 'final.json')
    """
    return os.path.join(get_submodule_root(), *relative_parts)
