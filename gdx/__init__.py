# coding: utf-8
# GAMS GDX interface
# 2012-06-18 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
"""
For those reading the code: Using the Python 'set' class makes the code in this
module simpler, but unfortunately leads to confusing semantics because the
'Set' is also one of the main types of GAMS symbols. To improve clarity in the
comments below, capitalized 'Set' is used for the latter.

TODO: document
(more TODOs scattered throughout)
"""
from os.path import dirname
from subprocess import check_output
from sys import maxsize

import pandas as pd

import gdxcc


# 'from gdx import *' will only bring these items into the namespace.
__all__ = [
    'enumarray',
    'set_data_type',
    'File',
    #'GDX',  # commented: no use in creating a GDX object directly, for now
    #'Symbol',    # commented: only reading supported at the moment. Creating
    #'Equation',  # these will make sense once writing is supported
    #'Set',
    #'Parameter',
    #'Variable',
    ]

# string representations of API constants for G(a)MS D(ata) T(ypes)
type_str = {
    gdxcc.GMS_DT_SET: 'set',
    gdxcc.GMS_DT_PAR: 'parameter',
    gdxcc.GMS_DT_VAR: 'variable',
    gdxcc.GMS_DT_EQU: 'equation',
    gdxcc.GMS_DT_ALIAS: None,  # aliases not created; see File.__init__()
    }

# string representations of API constants for G(a)MS VAR(iable) TYPE(s)
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

    Most methods in the API have similar semantics:

    * their names begin with gdx
    * the return value is a list where the first element is a return code

    This class hides these details, making for simpler code. Methods can be
    accessed in one of two ways:

    >>> g = GDX()
    >>> g.call('FileVersion') # call gdxFileVersion()
    >>> g.file_version()      # same
    """
    # methods that conform to the semantics of call()
    __valid = [
        'CreateD',
        'DataReadStr',
        'DataReadStrStart',
        'ErrorStr',
        'FileVersion',
        'OpenRead',
        'SymbolGetDomain',
        'SymbolInfo',
        'SymbolInfoX',
        'SystemInfo',
        ]

    def __init__(self):
        """Constructor."""
        self._handle = gdxcc.new_gdxHandle_tp()
        self.call('CreateD', GDX._gams_dir(), gdxcc.GMS_SSSIZE)

    def call(self, method, *args):
        """Invoke the GDX API method named 'gdx*method*'.

        Optional positional arguments *args* are passed to the API.
        """
        if method not in self.__valid:
            raise NotImplementedError(('GDX.call() cannot invoke '
                                       'gdxcc.gdx{}').format(method))
        ret = getattr(gdxcc, 'gdx{}'.format(method))(self._handle, *args)
        if ret[0]:
            # unwrap a 1-element array
            if len(ret) == 2:
                return ret[1]
            else:
                return ret[1:]
        else:
            error_str = self.call('ErrorStr', ret[1])
            if method == 'OpenRead' and (error_str ==
                                         'No such file or directory'):
                raise FileNotFoundError("[gdx{}] {}: '{}'".format(method,
                                                                  error_str,
                                                                  args[0]))
            else:
                raise Exception('gdx{}: {}'.format(method, error_str))

    def __getattr__(self, name):
        """Name mangling for method invocation without :func:`call`."""
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

        TODO: extend for Windows, Mac.
        """
        try:
            result = dirname(check_output(['which', 'gams'])).decode()
            return result
        except OSError:
            return ''


class File:
    """A GDX file.

    Load the file at *filename* into memory. *mode* must be 'r' (writing GDX
    files is not currently supported).

    If *match_domains* is True (the default), attempt to match each dimension
    of the domain of each GAMS Parameter and Variable to a Set in the same
    file.

    Once loaded, individual GAMS symbols are available as attributes of the
    File instance. For example, a GAMS parameter 'myparam' can be accessed:

    >>> f = File('example.gdx')
    >>> f.myparam.description
    'Example GAMS parameter'

    Symbols are also available through :func:`get_symbol` and
    :func:`get_symbol_by_index`.
    """
    def __init__(self, filename='', mode='r', lazy=False):
        """Constructor."""
        # load the GDX API
        self._lazy = lazy
        self._api = GDX()
        self._api.open_read(filename)
        self.version, self.producer = self._api.file_version()
        self.symbol_count, self.element_count = self._api.system_info()
        # read symbols
        self._symbols = {}
        self._index = [None for _ in range(self.symbol_count + 1)]
        for symbol_num in range(self.symbol_count + 1):
            name, _, type_code = self._api.symbol_info(symbol_num)
            name = name.lower()
            self._index[symbol_num] = name
            if type_code == gdxcc.GMS_DT_ALIAS:
                # aliases are stored as a reference to the aliased symbol
                _, __, desc = self._api.symbol_info_x(symbol_num)
                parent = desc.replace('Aliased with ', '').lower()
                assert parent in self._symbols
                self._symbols[name] = self._symbols[parent]
                continue
            elif type_code == gdxcc.GMS_DT_EQU:
                # equations: not yet implemented
                continue
            # create and store the symbol object
            self._symbols[name] = Symbol.create(type_code, self, symbol_num,
                                                lazy)

    def sets(self):
        """Return a list of all Set objects."""
        return list(filter(lambda s: isinstance(s, Set) and s.name != '*',
                           self._symbols.values()))

    def parameters(self):
        """Return a list of all Parameter objects."""
        return list(filter(lambda s: isinstance(s, Parameter),
                           self._symbols.values()))

    def get_symbol(self, name):
        """Retrieve the GAMS symbol *name*."""
        result = self._symbols[name]
        if self._lazy and not result._loaded:
            result.load()
        return result

    def get_symbol_by_index(self, index):
        """Retrieve the GAMS symbol stored at the *index* -th file position."""
        return self.get_symbol(self._index[index])

    def __getattr__(self, name):
        """Access symbols as object attributes."""
        try:
            return self.get_symbol(name)
        except KeyError as e:
            raise AttributeError(*e.args)

    def __getitem__(self, key):
        """Set element access."""
        if isinstance(key, str):
            return self.get_symbol(key)
        elif isinstance(key, int):
            return self.get_symbol_by_index(key)
        raise TypeError(key)


class Symbol:
    """Base class for GAMS symbols.

    To create a new symbol, use the factory method :py:meth:`.create`.

    All symbols have the following attributes:
    - name -- the symbol's name as declared in GAMS.
    - dim -- the number of dimensions.
    - records -- the number of entries in the symbol's data table.
    - description -- the description or explanatory text assigned to the symbol
      in GAMS
    """
    # True when symbol data has been loaded
    _loaded = False

    def __init__(self, gdxfile=None, index=0, lazy=False):
        """Constructor."""
        if gdxfile is None:
            raise NotImplementedError
        # Store references to the GDX API used to load this symbol
        self._file = gdxfile
        self._api = gdxfile._api
        self._index = index
        # Retrieve the name, dimension and type code
        self.name, self.dim, type_code = self._api.symbol_info(index)
        # Retrieve the length, variable type and description
        self.records, vartype, self.description = self._api.symbol_info_x(
            index)
        # Set the type
        self.gdx_type = type_str[type_code]
        if self.gdx_type == 'parameter':
            if self.dim == 0:
                self.gdx_type = 'scalar'
            self.gdx_type = '{} {}'.format(vartype_str[vartype], self.gdx_type)
        # Read the indices of the domain for this symbol
        self._domain_index = None if (self.dim == 0 or index == 0) else \
            self._api.symbol_get_domain(index)
        if lazy and isinstance(self, Parameter):
            return
        else:
            self.load()

    def load(self):
        if self._loaded:
            return
        # Read the elements of the domain directly.
        self._elements = [list() for _ in range(self.dim)]
        records = self._api.data_read_str_start(self._index)
        self._data = {}
        assert records == self.records
        for i in range(self.records):
            indices, value, afdim = self._api.data_read_str()
            for j, name in enumerate(indices):
                if name not in self._elements[j]:
                    self._elements[j].append(name)
            key = indices[0] if self.dim == 1 else tuple(indices)
            self._data[key] = value[gdxcc.GMS_VAL_LEVEL]
        self.domain = [None for _ in range(self.dim)]
        if self._index == 0:
            self._loaded = True
            return
        if self._domain_index is not None:
            # Some domain is specified for this Set
            for i, d in enumerate(self._domain_index):
                if i >= self.dim:
                    continue
                self.domain[i] = self._file.get_symbol_by_index(d)
                assert set(self.domain[i].idx).issuperset(self._elements[i])
        for i, d in enumerate(self.domain):
            if d not in (None, self._file['*']):
                continue
            candidate = range(maxsize)
            for s in self._file.sets() + [self._file['*']]:
                if s.dim > 1 or s == self:
                    continue
                # There is a bit of ambiguity here: could prefer the
                # highest-level non-* set, or the lowest level.
                elif (set(s.idx).issuperset(self._elements[i]) and len(s) <
                      len(candidate) and s.depth < getattr(candidate, 'depth',
                                                           maxsize)):
                    candidate = s
            if isinstance(candidate, Set):
                self.domain[i] = candidate

    def __str__(self):
        """Informal string representation of the Symbol."""
        return '{} {}({}): {}'.format(self.gdx_type.title(), self.name,
                                      ','.join([getattr(s, 'name', '?') for s
                                                in self.domain]),
                                      self.description)

    def __repr__(self):
        """Formal string representation of the Symbol."""
        return self.__str__()

    @staticmethod
    def create(type_code, gdxfile, index, lazy):
        """Create a new GAMS symbol.

        The created symbol is of one of the types named in type_str.
        *type_code* is one of gdxcc.GMS_DT_EQU, gdxcc.GMS_DT_PAR,
        gdxcc.GMS_DT_SET or gdxcc.GMS_DT_VAR. Symbol information and data are
        loaded from the symbol at position *index* of the File instance
        *gdxfile*.
        """
        return globals()[type_str[type_code].title()](gdxfile, index, lazy)


class Equation(Symbol):
    """Representation of a GAMS equation.

    TODO: implement this.
    """
    pass


class Set(Symbol):
    def load(self):
        Symbol.load(self)
        if self._index == 0 or self.dim == 1:
            self.idx = pd.Index(self._elements[0])
        else:
            elements = [list(d) for d in self.domain]
            self.idx = pd.MultiIndex.from_product(elements)

    @property
    def depth(self):
        """Return the 'depth' of this GAMS Set.

        The depth is the number of levels of inheritance between this set and
        GDX file's "root set." The following GAMS code::

          sets
            a    / a1, a2, a3, a4 /
            b(a) / a1, a2, a4 /
            c(b) / a2, a4/
            ;

        …the depth of set ``a`` is 1, the depth of set ``b`` is 2, and the
        depth of set ``c`` is 3.

        To assist :meth:`File._match_domain`, a large value is returned when
        the Set's domain is not available.
        """
        try:
            if self.name == '*':
                return 0
            return min([d.depth for d in filter(None, self.domain)]) + 1
        except ValueError:
            return maxsize
        except RuntimeError:
            print(self, self.domain)
            assert False

    # Implementations of special methods:
    __getattr__ = lambda self, name: getattr(self.idx, name)
    __getitem__ = lambda self, key: self.idx.__getitem__(key)
    __iter__ = lambda self: self.idx.__iter__()
    __len__ = lambda self: self.idx.__len__()


class Parameter(Symbol):
    """Representation of a GAMS parameter or variable.

    The values are accessible via indexing. For example, if 'myparam' is
    defined by the following GAMS code::

      sets
        x / x1, x2 /
        y / y1, y2 /
        ;
      parameter myparam(x,y)  / x1.y1 1000, x2.y2 2000 /;

    then it will be accessible as:

    >>> myparam = File('example.gdx').myparam
    >>> myparam['x1', 'y1']
    1000
    >>> myparam['x2', 'y2']
    2000

    For the moment, passing the incorrect number of indices will not get a
    subset of data; it will simply fail. Integer indexing is also not
    supported.
    """
    def load(self):
        Symbol.load(self)
        elements = [list(d) for d in self.domain] if self.dim > 0 else \
            [tuple()]
        self.data = pd.Series(self._data, pd.MultiIndex.from_product(elements))

    def __getattr__(self, name):
        if name == 'data':
            self.load()
            return self.data


# GAMS variables are currently functionally equivalent to parameters
Variable = Parameter
