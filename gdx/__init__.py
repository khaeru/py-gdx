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
from os.path import dirname
from subprocess import check_output
from sys import maxsize

import pandas as pd

import gdxcc


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
    gdxcc.GMS_DT_ALIAS: None,  # aliases not created; see File.__init__()
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
                assert False, method
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


class File:
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
        """Return a list of all :class:`Set` objects in this :class:`File`."""
        return list(filter(lambda s: isinstance(s, Set) and s.name != '*',
                           self._symbols.values()))

    def parameters(self):
        """Return a list of all :class:`Parameter` objects in this
        :class:`File`."""
        return list(filter(lambda s: isinstance(s, Parameter),
                           self._symbols.values()))

    def get_symbol(self, name):
        """Retrieve the :class:`Symbol` *name*."""
        result = self._symbols[name]
        if self._lazy and not result._loaded:
            result._load()
        return result

    def get_symbol_by_index(self, index):
        """Retrieve the :class:`Symbol` stored at the *index*-th position in
        the :class:`File`."""
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
    """Abstract base class for GAMS symbols.

    Specific GAMS objects, including :class:`Set` and :class:`Parameter`,
    inherit from :class:`Symbol`. To create a new symbol, use the factory
    method :py:meth:`.create`.

    All symbols have the following attributes:
    """
    # True when symbol data has been loaded
    _loaded = False

    def __init__(self, gdxfile=None, index=0, lazy=False):
        """Constructor, inherited by subclasses.
        
        *gdxfile* is the :class:`File` from which the symbol is to be loaded.
        *index* is the index of the Symbol in the file.
        If *lazy* is True (default: False), the data for the symbol is not
        loaded from the `File`; :class:`Set` is loaded immediately.
        """
        if gdxfile is None:
            raise NotImplementedError('Creating symbols outside of an '
                'existing GDX file is not supported')
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
        # Read the indices of the domain for this symbol. In most cases, this
        # only retrieves the index for the first dimension, necessitating the
        # checks in :func:`_load` (below).
        self._domain_index = None if (self.dim == 0 or index == 0) else \
            self._api.symbol_get_domain(index)
        if not (lazy and isinstance(self, Parameter)):  # Load data
            self._load()

    def _load(self):
        """Load Symbol data."""
        if self._loaded:
            return
        # Read the elements of the domain directly.
        records = self._api.data_read_str_start(self._index)
        assert records == self.records, ('gdxSymbolInfoX ({}) and '
            'gdxDataReadStrStart ({}) disagree on number of records in {}'
            ).format(self.records, records, self.name)
        # Indices of data records, one list per dimension
        self._elements = [list() for _ in range(self.dim)]
        # Data points. Keys are index tuples, values are data. For a 1-D
        # :class:`Set`, the data is the GDX 'string number' of the text
        # associated with the element.
        self._data = {}
        # Loop over all records
        for i in range(self.records):
            indices, value, afdim = self._api.data_read_str()  # Next record
            # Update _elements with the indices
            for j, name in enumerate(indices):
                if name not in self._elements[j]:
                    self._elements[j].append(name)
            # Convert a 1-D index from a tuple to a bare string
            key = indices[0] if self.dim == 1 else tuple(indices)
            # The value is a sequence, containing the level, marginal, lower &
            # upper bounds, etc. Store only the value (first element).
            self._data[key] = value[gdxcc.GMS_VAL_LEVEL]
        # Domain of the symbol. The length of the domain is the same as the
        # dimension; each element is either a reference to a :class:`Set`, or
        # None.
        self.domain = [None for _ in range(self.dim)]
        if self._index == 0:  # Universal set: nothing further to do
            self._loaded = True
            return
        # If domain is specified for this Set, try to use this information
        if self._domain_index is not None:
            for i, d in enumerate(self._domain_index):
                if i >= self.dim:
                    continue
                # Retrieve the symbol referred to by the domain index and
                # check that it contains the elements in this Symbol
                self.domain[i] = self._file.get_symbol_by_index(d)
                assert set(self.domain[i].idx).issuperset(self._elements[i])
        # Compute the domain directly, for each dimension.
        for i, d in enumerate(self.domain):
            if d not in (None, self._file['*']):
                # Already set for this dimension
                continue
            # Check each other Set which could be a domain
            candidate = range(maxsize)
            for s in self._file.sets() + [self._file['*']]:
                if s.dim > 1 or s == self or s.domain == [self]:
                    # s doesn't work as as a domain for this dimension:
                    # multidimensional, same Set, or it has the current Set as
                    # its domain (recursion)
                    continue
                elif ((set(s.idx).issuperset( self._elements[i]) and
                      len(s) < len(candidate) and
                      s.depth < getattr(candidate, 'depth', maxsize))):
                    # s is a better match than candidate for the domain:
                    # Is a superset of the elements on this dimension, is
                    # smaller, and is at a low 'depth' (closer to '*').
                    candidate = s
            # Best candidate is this Symbol's domain for the current dimension
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
    """Representation of a GAMS set.

    Set elements are accessble via indexing. For example, if 'myset' is defined
    by the following GAMS code::

      set myset / abc, def, ghi /;

    then it will be accessible as:

    >>> myset = File('example.gdx').myset
    >>> myset[2]
    'ghi'
    >>> myset[:]
    ['abc', 'def', 'ghi']

    Note that because Python uses 0-based indexing, indices will be one lower
    than those used with the GAMS ord() function.
    """
    #: A :py:class:`pandas.Index` or :py:class:`pandas.MultiIndex` representing
    #: the Set.
    idx = None

    def _load(self):
        """Load Set data."""
        # Populate _elements and data for following code
        Symbol._load(self)
        # Construct a pandas Index or MultiIndex to represent the set
        if self._index == 0 or self.dim == 1:
            # Universal set, or a 1-D Set → Index
            self.idx = pd.Index(self._elements[0])
        else:
            # Multi-dimensional Set → MultiIndex
            elements = [list(d) for d in self.domain]
            self.idx = pd.MultiIndex.from_product(elements)
        # Attempt to load the explanatory text/description for the Set's
        # elements.
        self._text = None
        # self._data (see `Symbol._load()`) contains either 0 (for the
        # universal set ('*') and subsets), or an index for the element text
        # (all top-level sets).
        if self.dim == 1:  # Don't load for multi-dimensional sets
            text = {}
            for k, v in self._data.items():
                if v > 0:
                    text[k] = self._api.get_elem_text(int(v))[0]
            if len(text):
                self._text = pd.Series(text, index=self.idx)
        self._loaded = True

    @property
    def depth(self):
        """The 'depth' of this GAMS Set.

        The depth is the number of levels of inheritance between this set and
        GDX file's universal set, ``*``. In the following GAMS code::

          sets
            a    / a1, a2, a3, a4 /
            b(a) / a1, a2, a4 /
            c(b) / a2, a4/
            ;

        …the depth of set ``a`` is 1, the depth of set ``b`` is 2, and the
        depth of set ``c`` is 3.

        When the Set's domain undefinited, depth is set to
        :py:class:`sys.maxsize`.
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

    # Implementations of special methods: direct access to the pandas data
    # structure
    __getattr__ = lambda self, name: getattr(self.idx, name)
    __iter__ = lambda self: self.idx.__iter__()
    __len__ = lambda self: self.idx.__len__()

    def __getitem__(self, key):
        """Implementation of __getitem__.
        
        If :class:`Set` are passed in *key*, refer to their underlying
        pd.Index.
        """
        try:
            key_ = [k if not isinstance(k, Set) else k.idx for k in key]
        except TypeError:
            key_ = key
        return self.idx.__getitem__(key_)

    #: For backwards compatibility
    def index(self, key):
        try:
            return self.idx.get_loc(key)
        except KeyError as e:
            raise ValueError(*e.args)


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
    #: A :py:class:`pandas.Series` containing the parameter data. 
    data = None

    def _load(self):
        """Load Parameter data."""
        # Populate _elements and data for following code
        Symbol._load(self)
        if self.dim == 0:
            self.data = self._data[tuple()]
        else:
            # Elements for a pandas MultiIndex for this set.
            # pd.MultiIndex.from_product will produce a pd.Index if the length
            # of the argument is 1 (i.e. if self.dim == 1)
            elements = [list(d) for d in self.domain] if self.dim > 0 else \
                [tuple()]
            names = [d.name for d in self.domain] if self.dim > 0 else [
                                                                       tuple()]
            self.data = pd.Series(self._data, pd.MultiIndex.from_product(
                                  elements, names=names))
        self._loaded = True

    def __getattr__(self, name):
        if name == 'data':
            self._load()
            return self.data

    # Implementations of special methods:
    # Direct access to the pandas data structure
    __getattr__ = lambda self, name: getattr(self.data, name)
    __iter__ = lambda self: self.data.__iter__()
    __len__ = lambda self: self.data.__len__()

    def __getitem__(self, key):
        """Implementation of __getitem__.
        
        If :class:`Set` are passed in *key*, refer to their underlying
        pd.Index.
        """
        if isinstance(key, (list, tuple)):
            key_ = [k if not isinstance(k, Set) else k.idx for k in key]
        else:
            key_ = key
        return self.data.ix[key_]

    # Methods for 0-dimensional Parameters (i.e. scalars)
    def __float__(self):
        if self.dim > 0:
            raise ValueError(('Cannot convert {}-dimensional Parameter to '
                              'float').format(self.dim))
        return self.data

    # More numeric methods based on __float__
    __int__ = lambda self: int(float(self))
    __lt__ = lambda self, other: float(self).__lt__(other)
    __le__ = lambda self, other: float(self).__le__(other)
    __gt__ = lambda self, other: float(self).__gt__(other)
    __ge__ = lambda self, other: float(self).__ge__(other)

    def __eq__(self, other):
        """Implementation of __eq__.

        * Compare using __float__ when it has meaning and the other object is
          numeric.
        * Compare as identity with another Symbol or None.
        """
        if self.dim == 0 and isinstance(other, (int, float, complex)):
            return float(self).__eq__(other)
        elif isinstance(other, Symbol):
            return self._index == other._index
        elif other is None:
            return False
        else:
            raise NotImplementedError(('Cannot compare Parameter with '
                                       '{}.').format(type(other)))

    # Inequality: inverse of __eq__
    __ne__ = lambda self, other: not self.__eq__(other)


# GAMS variables are currently functionally equivalent to parameters
Variable = Parameter
