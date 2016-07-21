import sys

from builtins import filter, range, object, super, zip
from future.standard_library import install_aliases

PY3 = sys.version_info[0] >= 3

if PY3:
    from builtins import FileNotFoundError
    from shutil import which
else:
    class FileNotFoundError(OSError):
        pass
    from backports.shutil_which import which
