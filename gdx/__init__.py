# coding: utf-8
# GAMS GDX interface
# 2012-06-18 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
"""

.. note::
   For those reading the code: Using the Python 'set' class makes the code in
   this module simpler, but unfortunately leads to confusing semantics because
   the 'Set' is also one of the main types of GAMS symbols. To improve clarity
   in the comments, capitalized 'Set' is used for the latter.
"""
from collections import OrderedDict
from itertools import chain, zip_longest
import logging
from logging import debug
from os.path import dirname
from subprocess import check_output
from sys import exit, maxsize

from numpy import full, nan
from pandas import Index, MultiIndex, Series
from xray import DataArray, Dataset

import gdxcc


logging.basicConfig(level=logging.DEBUG)

# 'from gdx import *' will only bring these items into the namespace.
__all__ = [
    'File',
    'GDX',
    #'Symbol',    # commented: only reading supported at the moment. Creating
    #'Equation',  # these will make sense once writing is supported
    #'Set',
    #'Parameter',
    #'Variable',
    'type_str',
    ]

#: String representations of API constants for G(a)MS D(ata) T(ypes)
type_str = {
    gdxcc.GMS_DT_SET: 'set',
    gdxcc.GMS_DT_PAR: 'parameter',
    gdxcc.GMS_DT_VAR: 'variable',
    gdxcc.GMS_DT_EQU: 'equation',
    gdxcc.GMS_DT_ALIAS: 'alias',  # aliases not created; see File.__init__()
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


class GDX:
    """Basic wrapper around the GDX API.

    Most methods in the GDX API have similar semantics:

    * All method names begin with `gdx`.
    * Most methods return a list where the first element is a return code.

    This class hides these details, allowing for simpler code. Methods can be
    accessed using :func:`call`:

    >>> g = GDX()
    >>> g.call('FileVersion') # call gdxFileVersion()

    Alternately, they can be accessed as "Pythonic" members of GDX objects,
    where CamelCase is replaced by lowercase, with underscores separating
    words.

    >>> g.file_version()      # same as above

    """
    #: Methods that conform to the semantics of :func:`call`
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
        self.call('CreateD', GDX._gams_dir(), gdxcc.GMS_SSSIZE)

    def call(self, method, *args):
        """Invoke the GDX API method named gdx*method*.

        Optional positional arguments *args* are passed to the API method.
        Returns the result of the method call, or raises an appropriate
        exception.
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
#                assert False, method
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

    @staticmethod
    def _gams_dir():
        """Locate GAMS on a POSIX system.

        The path to the GAMS executable is a required argument of
        ``gdxCreateD``, the method for connecting to the GDX API.

        .. todo::

           This function relies on the shell utility `which`, and will probably
           not work on Windows. Extend.
        """
        try:
            result = dirname(check_output(['which', 'gams'])).decode()
            return result
        except OSError:
            return ''


class File(Dataset):
    """A GDX file.

    Load the file at *filename* into memory. *mode* must be 'r' (writing GDX
    files is not currently supported). If *lazy* is ``True`` (the default),
    then the data for any GAMS parameter is not loaded until the parameter is
    first accessed. For large files, this makes loading significantly faster.

    Individual GAMS symbols are available in one of three ways:

    1. Using :func:`get_symbol`.
    2. Using :func:`get_symbol_by_index`.
    3. As attributes of the File instance. For example, a GAMS parameter
       'myparam' can be accessed:

       >>> f = File('example.gdx')
       >>> f.myparam.description
       'Example GAMS parameter'
    """
    def __init__(self, filename='', mode='r'):
        """Constructor."""
        Dataset.__init__(self)
        # load the GDX API
        self._api = GDX()
        api = self._api
        api.open_read(filename)
        v, p = api.file_version()
        sc, ec = api.system_info()
        self.attrs['version'] = v.strip()
        self.attrs['producer'] = p.strip()
        self.attrs['symbol_count'] = sc
        self.attrs['element_count'] = ec
        self._symbols = {}
        self._index = [None for _ in range(sc + 1)]
        self._scalar = {}
        # Read symbols
        [self._load_symbol(s_num) for s_num in range(sc + 1)]

    def _load_symbol(self, index):
        if self._index[index] in self._symbols:
            debug('_load_symbol({}): already loaded'.format(index))
            return
        api = self._api

        # Read information about the symbol
        name, dim, type_code = api.symbol_info(index)
        n_records, vartype, desc = api.symbol_info_x(index)
        debug('symbol_info({}): {} — {}-dim — {}'.format(index,
                                                          name, dim, type_str[type_code]))
        debug('symbol_info_x({}): {} — {} — {}'.format(index,
                                                      n_records, vartype, desc))

        # Equations and aliases require limited processing
        if type_code == gdxcc.GMS_DT_EQU:
            debug('{}: loading of GMS_DT_EQU not implemented'.format(name))
            return
        elif type_code == gdxcc.GMS_DT_ALIAS:
            parent = self[desc.replace('Aliased with ', '')]
            if parent.attrs['_gdx_type_code'] == gdxcc.GMS_DT_SET:
                Dataset.__setitem__(self, name, parent.copy())
                Dataset.set_coords(self, name, inplace=True)
            else:
                # TODO fix this
                assert False
                self._alias[name] = parent
            return

        # Common code for sets, parameters and variables
        # Set the type
        gdx_type = type_str[type_code]
        if gdx_type == 'parameter':
            if dim == 0:
                gdx_type = 'scalar'
            gdx_type = '{} {}'.format(vartype_str[vartype], gdx_type)

        # Read the domain of the set, as a list of names
        try:
            domain = api.symbol_get_domain_x(index)
        except Exception as e:
            assert name == '*'
            domain = []

        # Read the elements of the domain directly.
        n_records2 = self._api.data_read_str_start(index)
        assert n_records == n_records2, ('{}: gdxSymbolInfoX ({}) and '
            'gdxDataReadStrStart ({}) disagree on number of records.'
            ).format(name, n_records, n_records2)

        # Indices of data records, one list per dimension
        elements = [list() for _ in range(dim)]
        # Data points. Keys are index tuples, values are data. For a 1-D
        # :class:`Set`, the data is the GDX 'string number' of the text
        # associated with the element.
        data = {}
        try:
            while True:  # Loop over all records
                labels, value, _ = self._api.data_read_str()  # Next record
                # Update elements with the indices
                for j, label in enumerate(labels):
                    if label not in elements[j]:
                        elements[j].append(label)
                # Convert a 1-D index from a tuple to a bare string
                key = labels[0] if dim == 1 else tuple(labels)
                # The value is a sequence, containing the level, marginal, lower
                # & upper bounds, etc. Store only the value (first element).
                data[key] = value[gdxcc.GMS_VAL_LEVEL]
        except Exception as e:
            if len(data) == n_records:
                pass
            else:
                raise

        # Domain as a list of references
        domain_ = [None for _ in range(dim)]
        # If domain is specified for the symbol, try to use that information
        for i, d in enumerate(domain):
            if d != '*':
                domain_[i] = self[d]
                assert set(domain_[i].values).issuperset(elements[i])
                continue
            # Compute the domain directly for this dimension
            candidate = self[d]
            for s in self.coords.values():
                print(s.name)
                if s.ndim > 1 or s.name == name or (s.attrs['_gdx_domain'] ==
                                                                        [self]):
                    # s doesn't work as as a domain for this dimension:
                    # multidimensional, same Set, or it has the current Set as
                    # its domain (recursion)
                    continue
                elif (set(s.values).issuperset(elements[i]) and
                      len(s) < len(candidate) and
                      s.attrs['_gdx_index'] < candidate.attrs['_gdx_index']):
                    # s is a better match than candidate for the domain: it is a
                    # superset of the elements on this dimension, is smaller,
                    # and is at a low 'depth' (closer to '*').
                    debug('{} dim {} ("{}"): prefer {} to {}'.format(name, i, d, s.name, candidate.name))
                    candidate = s
            # Best candidate is this Symbol's domain for the current
            # dimension
            domain_[i] = candidate
        if len(domain):
            debug('{} {}'.format(domain, list([d.name for d in domain_])))
        # TODO domain_ doesn't yet actually DO anything

        # Continue loading
        if type_code == gdxcc.GMS_DT_SET:
            if dim > 1:
                Dataset.__setitem__(self, name, self._to_dataarray(domain,
                                                                   elements, data,
                                                                   'set'))
            else:
                Dataset.__setitem__(self, name, elements[0])
            Dataset.set_coords(self, name, inplace=True)
        elif type_code in (gdxcc.GMS_DT_PAR, gdxcc.GMS_DT_VAR):
            if dim == 0:
                self._scalar[name] = data.popitem()
                return
            else:
                try:
                    temp = self._to_dataarray(domain, elements, data)
                    Dataset.__setitem__(self, name, temp)
                except ValueError:
                    print(temp, '\n\n', self, '\n\n', self['*'].values)
                    raise
        # TODO these are not saved for scalars
        self[name].attrs['_gdx_domain'] = domain
        self[name].attrs['_gdx_index'] = index
        self[name].attrs['_gdx_type_code'] = type_code

    def _to_dataarray(self, domain, elements, data, mode='parameter'):
        assert mode in ('set', 'parameter')
        # To satisfy xray.DataArray.__init__, two dimensions must not have the
        # same name unless they have the same length. Construct a 'fake'
        # universal set.
        if sum(map(lambda d: d=='*', domain)) > 1:
            dim = range(len(domain))
            star = set(chain(*[elements[i] for i in dim if domain[i] == '*' and
                                len(elements[i])]))
            elements = [star if domain[i] == '*' else elements[i] for i in dim]
        kwargs = {}
        fill = nan
        if mode == 'set':
            data = dict(zip_longest(data.keys(), [True], fillvalue=True))
            fill = False
            kwargs['dtype'] = bool
        # Dummy data
        if len(data) == 0:
            key = tuple([self[d].values[0] for d in domain])
            data[key] = fill
        # Construct the index
        if len(domain) == 1:
            idx = Index(data.keys(), name=domain[0])
        elif len(data) == 1:
            idx = MultiIndex.from_tuples([data.keys()], names=domain)
        else:
            idx = MultiIndex.from_tuples(data.keys(), names=domain)
        return DataArray.from_series(Series(data, index=idx, **kwargs))

    # def sets(self):
    #     """Return a list of all :class:`Set` objects in this :class:`File`."""
    #     return list(filter(lambda s: isinstance(s, Set) and s.name != '*',
    #                        self._symbols.values()))
    #
    # def parameters(self):
    #     """Return a list of all :class:`Parameter` objects in this
    #     :class:`File`."""
    #     return list(filter(lambda s: isinstance(s, Parameter),
    #                        self._symbols.values()))

    def get_symbol_by_index(self, index):
        """Retrieve the :class:`Symbol` stored at the *index*-th position in
        the :class:`File`."""
        return self[self._index[index]]

    def __getattr__(self, name):
        """Access symbols as object attributes."""
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(*e.args)

    def __getitem__(self, key):
        """Set element access."""
        try:
            return Dataset.__getitem__(self, key)
        except KeyError as e:
            if isinstance(key, int):
                return self.get_symbol_by_index(key)
            else:
                raise
