import sys

from builtins import filter, range, object, super, zip
from future.standard_library import install_aliases
from future.utils import raise_from

PY3 = sys.version_info[0] >= 3

if PY3:
    from builtins import FileNotFoundError
    from shutil import which
else:  # pragma: no cover
    class FileNotFoundError(OSError):
        pass
    from backports.shutil_which import which
