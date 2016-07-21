import sys

PY3 = sys.version_info[0] >= 3

if PY3:
    from builtins import FileNotFoundError
else:
    class FileNotFoundError(OSError):
        pass

__all__ = ['FileNotFoundError']
