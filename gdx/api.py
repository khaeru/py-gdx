# coding: utf-8
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from os.path import dirname
import sys

import gdxcc

from .pycompat import FileNotFoundError, install_aliases, object, which
install_aliases()


__all__ = [
    'GDX',
    'gdxcc',
    'type_str',
    'vartype_str',
    ]


#: String representations of API constants for G(a)MS D(ata) T(ypes)
type_str = {
    gdxcc.GMS_DT_SET: 'set',
    gdxcc.GMS_DT_PAR: 'parameter',
    gdxcc.GMS_DT_VAR: 'variable',
    gdxcc.GMS_DT_EQU: 'equation',
    gdxcc.GMS_DT_ALIAS: 'alias',
    }


#: String representations of API constants for G(a)MS VAR(iable) TYPE(s)
vartype_str = {
    gdxcc.GMS_VARTYPE_UNKNOWN: 'unknown',
    gdxcc.GMS_VARTYPE_BINARY: 'binary',
    gdxcc.GMS_VARTYPE_INTEGER: 'integer',
    gdxcc.GMS_VARTYPE_POSITIVE: 'positive',
    gdxcc.GMS_VARTYPE_NEGATIVE: 'negative',
    gdxcc.GMS_VARTYPE_FREE: 'free',
    gdxcc.GMS_VARTYPE_SOS1: 'sos1',
    gdxcc.GMS_VARTYPE_SOS2: 'sos2',
    gdxcc.GMS_VARTYPE_SEMICONT: 'semicont',
    gdxcc.GMS_VARTYPE_SEMIINT: 'semiint',
    gdxcc.GMS_VARTYPE_MAX: 'max',
    }


def _gams_dir():
    """Locate GAMS on a POSIX system.

    Returns the path to the  executable is a required argument of
    ``gdxCreateD``, the method for connecting to the GDX API.
    """
    return dirname(which('gams'))


class GDX(object):
    """Wrapper around the `GDX API`_."""
    #: Methods that conform to the semantics of :func:`call`.
    __valid = [
        'CreateD',
        'DataReadStr',
        'DataReadStrStart',
        'ErrorCount',
        'ErrorStr',
        'FileVersion',
        'GetElemText',
        'GetLastError',
        'OpenRead',
        'SymbolGetDomain',
        'SymbolGetDomainX',
        'SymbolInfo',
        'SymbolInfoX',
        'SystemInfo',
        ]

    def __init__(self):
        """Constructor."""
        self._handle = gdxcc.new_gdxHandle_tp()
        self.error_count = 0
        self.call('CreateD', str(_gams_dir()), gdxcc.GMS_SSSIZE)

    def call(self, method, *args):
        """Invoke the GDX API method named gdx\ *Method*.

        Optional positional arguments *args* are passed to the API method.
        Returns the result of the method call, with the return code stripped.
        Refer to the GDX API documentation for the type and number of arguments
        and return values for any method.

        If the call fails, raise an appropriate exception.

        """
        if method not in self.__valid:
            raise NotImplementedError(('GDX.call() cannot invoke '
                                       'gdxcc.gdx{}').format(method))
        ret = getattr(gdxcc, 'gdx{}'.format(method))(self._handle, *args)
        if isinstance(ret, int):
            return ret
        if ret[0]:
            # unwrap a 1-element array
            if len(ret) == 2:
                return ret[1]
            else:
                return ret[1:]
        else:
            if method == 'OpenRead':
                error_str = self.call('ErrorStr', ret[1])
                if error_str == 'No such file or directory':
                    raise FileNotFoundError("[gdx{}] {}: '{}'".format(method,
                                            error_str, args[0]))
            else:
                error_count = self.call('ErrorCount')
                if error_count > self.error_count:
                    self.error_count = error_count
                    error_num = self.call('GetLastError')
                    error_str = self.call('ErrorStr', error_num)
                    raise Exception('[gdx{}] {}'.format(method, error_str))
                else:
                    raise RuntimeError(('[gdx{}] returned {} for arguments {}'
                                        ).format(method, args, ret))

    def __getattr__(self, name):
        """Name mangling for method invocation without call()."""
        mangle = name.title().replace('_', '')
        if mangle in self.__valid:
            def wrapper(*args):
                return self.call(mangle, *args)
            return wrapper
        else:
            raise AttributeError(name)
