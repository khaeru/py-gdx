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
import sys
if sys.version_info[0] >= 3:
    from queue import Queue
else:
    from Queue import Queue

from .enumarray import enumarray
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

NULL = None
RETURN = lambda x: x


def set_data_type(t):
    global NULL, RETURN
    if t == 'plain':
        NULL = None
        RETURN = lambda x: x
    elif t == 'numpy':
        import numpy
        NULL = numpy.NaN
        RETURN = lambda x: numpy.array(x)
    else:
        raise ValueError

set_data_type('plain')


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
            raise Exception('gdx{}: {}'.format(method, self.call('ErrorStr',
                            ret[1])))

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
            result = dirname(check_output(['which', 'gams']))
            if sys.version_info[0] >= 3:
                result = result.decode()
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
    def __init__(self, filename='', mode='r', match_domains=True, lazy=False):
        """Constructor."""
        self._match_domains = match_domains
        self._symbols = {}
        self._index = {}
        # load the GDX API
        self._api = GDX()
        # TODO: check that 'filename' exists
        self._api.open_read(filename)
        self.version, self.producer = self._api.file_version()
        self.symbol_count, self.element_count = self._api.system_info()
        # read symbols
        set_queue = Queue()
        for symbol_num in range(self.symbol_count + 1):
            name, junk, type_code = self._api.symbol_info(symbol_num)
            name = name.lower()
            self._index[symbol_num] = name
            if type_code == gdxcc.GMS_DT_ALIAS:
                # aliases are stored as a reference to the aliased symbol
                junk, junk2, desc = self._api.symbol_info_x(symbol_num)
                parent = desc.replace('Aliased with ', '').lower()
                assert parent in self._symbols
                self._symbols[name] = self._symbols[parent]
                continue
            elif type_code == gdxcc.GMS_DT_EQU:
                # equations: not yet implemented
                continue
            # create the symbol object
            symbol = Symbol.create(type_code, self, symbol_num)
            # load Sets immediately
            if isinstance(symbol, Set):
                symbol._load()
                # put Sets into a queue
                set_queue.put(symbol)
            # store the object
            self._symbols[name] = symbol
        # process Sets. Because symbols are not stored in any particular order
        # in the GDX file, Sets are not necessarily loaded before others which
        # reference them as domain dimensions. In order to make multiple
        # passes, use a queue and reinsert objects which need to be rechecked
        while not set_queue.empty():
            symbol = set_queue.get()
            # try to match the domain
            if not self._match_domain(symbol):
                # unsuccessful, return to the queue
                set_queue.put(symbol)
        # process Parameters (also Variables, because of class inheritance, see
        # below). Load and optionally match the domain
        if not lazy:
            for symbol in self.parameters():
                symbol._load()
                if self._match_domains:
                    self._match_domain(symbol)

    def sets(self):
        """Return a list of all Set objects."""
        if sys.version_info[0] >= 3:
            values = self._symbols.values()
        else:
            values = self._symbols.itervalues()
        return list(filter(lambda s: isinstance(s, Set) and s.name != '*',
                    values))

    def parameters(self):
        """Return a list of all Parameter objects."""
        if sys.version_info[0] >= 3:
            values = self._symbols.values()
        else:
            values = self._symbols.itervalues()
        return list(filter(lambda s: isinstance(s, Parameter), values))

    def _match_domain(self, symbol):
        """Match each dimension of the domain of *symbol* to a GAMS Set."""
        # TODO: make this method less terribly slow
        if symbol.dim == 0 or hasattr(symbol, 'domain') or symbol.name == '*':
            # domain is always OK:
            # - for scalars
            # - if the 'domain' attribute was previously set
            # - for the root set
            return True
        # grab some information about the symbol
        s = symbol.domain_sets()
        # domain_index contains the indexes of each of the symbols in this
        # symbol's domain
        domain_index = symbol._domain_index
        # placeholders for the domain
        domain = [None] * symbol.dim

        def valid_parent(parent_symbol, child_symbol, domain_set):
            """Shortcut method.

            A candidate *parent_symbol* is a match for a particular domain
            dimension of *child_symbol* with elements *domain_set* iff:

            * it is one-dimensional
            * it is not the same object as *child_symbol*
            * it does not have *child_symbol* as a member of its own domain
              (avoid circular references)
            * its elements are a superset of the elements in the *domain_set*

            More computationally intensive conditions are placed last.
            """
            return parent_symbol.dim == 1 \
                and parent_symbol != child_symbol \
                and child_symbol not in getattr(parent_symbol, 'domain', []) \
                and parent_symbol.domain_sets()[0].issuperset(domain_set)
        # the reported dimension (from gdxSymbolInfo) and the dimension of
        # actual data (from gdxDataReadStr) always agree, but the reported
        # domain (from gdxSymbolGetDomain) can be incorrect. See which is the
        # case:
        if len(s) == len(domain_index):
            # the reported domain is at least the correct *length*. Check each
            # item in turn
            for i, d in enumerate(domain_index):
                parent = self._symbols[self._index[d]]
                s2 = parent.domain_sets()
                if len(s2) == 1 and s2[0].issuperset(s[i]):
                    domain[i] = parent
                    continue
            # if there are 'None' elements in domain at this point, then the
            # info reported by the API was wrong
        else:
            # the reported domain is not the correct length; need to guess
            for i in range(symbol.dim):
                # if there is no content along this dimension, there is no
                # basis for guessing. Use the root set by default
                if len(s[i]) == 0:
                    domain[i] = self._symbols['*']
                    continue
                # try the sets from the reported domain, in case one of them is
                # actually correct
                candidates = set()
                for d in filter(lambda j: j != 0, domain_index):
                    parent = self.get_symbol_by_index(d)
                    if valid_parent(parent, symbol, s[i]):
                        candidates.add(parent)
                # one of them matched; might as well go with it
                if len(candidates) == 1:
                    domain[i] = candidates.pop()
                    continue
                else:
                    # either zero or >2 matches; in the latter case, code below
                    # will give a better result. Clear the result
                    candidates = set()
                # second heuristic: try *all* sets
                for parent in self.sets():
                    if valid_parent(parent, symbol, s[i]):
                        candidates.add(parent)
                if len(candidates) == 0:
                    # really have no clue at this point, use *
                    domain[i] = self._symbols['*']
                    continue
                elif len(candidates) == 1:
                    domain[i] = candidates.pop()
                    continue
                # two or more Sets are candidates
                # the highest-level Set
                best = min([c.depth for c in candidates])
                c2 = list(filter(lambda c: c.depth == best, candidates))
                if len(c2) == 1:
                    domain[i] = c2.pop()
                    continue
                # the largest set. This is highly arbitrary; could also use the
                # smallest set
                largest = max([len(c.elements) for c in c2])
                c3 = list(filter(lambda c: len(c.elements) == largest, c2))
                if len(c3) == 1:
                    domain[i] = c3.pop()
        if domain.count(None) == 0:
            symbol.domain = domain
            return True
        else:
            return False

    def get_symbol(self, name):
        """Retrieve the GAMS symbol *name*."""
        return self._symbols[name]

    def get_symbol_by_index(self, index):
        """Retrieve the GAMS symbol stored at the *index* -th file position."""
        return self._symbols[self._index[index]]

    def __getattr__(self, name):
        """Access symbols as object attributes."""
        if name in self._symbols:
            if not self._symbols[name]._loaded:
                self._symbols[name]._load()
                if self._match_domains:
                    self._match_domain(self._symbols[name])
            return self._symbols[name]
        else:
            raise AttributeError(name)

    def __getitem__(self, key):
        """Set element access."""
        return self.__getattr__(key)


class Symbol:
    """Base class for GAMS symbols.

    To create a new symbol, use the factory method :py:meth:`.create`.
    """
    # True when symbol data has been loaded
    _loaded = False

    def __init__(self, gdxfile=None, index=0):
        """Constructor."""
        if gdxfile:
            self._api = gdxfile._api
            self._index = index
        self.name, self.dim, type_code = self._api.symbol_info(index)
        self.records, userinfo, self.description = self._api.symbol_info_x(
            index)
        # set the type
        self.type = type_str[type_code]
        if self.type == 'parameter':
            if self.dim == 0:
                self.type = 'scalar'
            self.type = '{} {}'.format(vartype_str[userinfo], self.type)
        if self.dim > 0 and index != 0:
            self._domain_index = self._api.symbol_get_domain(index)

    def _load(self):
        """Load symbol data.

        Each subclass must overload this method to read and store the symbol's
        data through the API. Currently File.__init__ forcibly loads all
        defined symbols, but a clever hacker could implement lazy-loading,
        whereby data or even symbol information are only loaded upon access.
        """
        raise NotImplementedError

    def __str__(self):
        return '{} {}({}): {}'.format(self.type.title(), self.name,
               ','.join([s.name for s in self.domain]), self.description)

    def __repr__(self):
        return '{} {}({}): {}'.format(self.type.title(), self.name,
               ','.join([s.name for s in self.domain]), self.description)

    def domain_sets(self):
        """Return a list of sets with the domain of GAMS symbol data.

        Every subclass must overload this method to return a list of length
        Symbol.dim. Each list element is a Python set containing every value
        for that domain dimension in the GAMS symbol.

        For simple GAMS Sets, these are equivalent to the set itself; but for
        Parameters, Variables, or GAMS subsets (especially multidimensional
        subsets) they may be smaller or empty.
        """
        raise NotImplementedError

    @staticmethod
    def create(type_code, gdxfile, index):
        """Create a new GAMS symbol.

        The created symbol is of one of the types named in type_str.
        *type_code* is one of gdxcc.GMS_DT_EQU, gdxcc.GMS_DT_PAR,
        gdxcc.GMS_DT_SET or gdxcc.GMS_DT_VAR. Symbol information and data are
        loaded from the symbol at position *index* of the File instance
        *gdxfile*.
        """
        return globals()[type_str[type_code].title()](gdxfile, index)


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
    def _load(self):
        """Implementation of Symbol._load()."""
        # don't load twice
        if self._loaded:
            return
        elements = []
        self.unordered = [set() for i in range(self.dim)]
        records = self._api.data_read_str_start(self._index)
        for i in range(records):
            indices, value, afdim = self._api.data_read_str()
            if self.dim == 1:
                elements.append(indices[0])
                self.unordered[0].add(indices[0])
            else:
                elements.append(tuple(indices))
                for j in range(self.dim):
                    self.unordered[j].add(indices[j])
        # TODO possibly change this once Set objects are writeable
        self.elements = tuple(elements)
        self._loaded = True

    def domain_sets(self):
        """Implementation of Symbol.domain_sets()."""
        return self.unordered

    def __getitem__(self, key):
        """Set element access."""
        return self.elements[key]

    def __iter__(self):
        """TODO check behaviour with multidimensional sets"""
        return iter(self.elements)

    def __len__(self):
        """Implementation of __len__"""
        return len(self.elements)

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
        if self.name == '*':
            return 0
        elif hasattr(self, 'domain'):
            return min([d.depth for d in self.domain]) + 1
        else:
            return 1000

    def index(self, key):
        """Shorthand to get the index of *key* in self.elements."""
        return self.elements.index(key)

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
    def _load(self):
        """Implementation of Symbol._load()."""
        # don't load twice
        if self._loaded:
            return
        self._data = {}
        records = self._api.data_read_str_start(self._index)
        for i in range(records):
            indices, value, afdim = self._api.data_read_str()
            if self.dim == 1:
                indices = indices[0]
            else:
                indices = tuple(indices)
            self._data[indices] = value[gdxcc.GMS_VAL_LEVEL]
        if self.dim == 0:
            self.domain = []
        self._loaded = True

    def domain_sets(self):
        """Implementation of Symbol.domain_sets()."""
        result = [set() for i in range(self.dim)]
        for key in self._data.keys():
            if self.dim == 1:
                key = (key,)
            for i in range(self.dim):
                result[i].add(key[i])
        return result

    def _enumarray(self):
        self._value = enumarray(self.domain)
        for k, v in self._data.items():
            self._value[k] = v

    def __getitem__(self, key):
        """Attribute access method.

        TODO: add more indexing features
        """
        if not hasattr(self, '_value'):
            self._enumarray()
        return self._value[key]

    def __setitem__(self, key, value):
        if not hasattr(self, '_value'):
            self._enumarray()
        self._value[key] = value

#    if type(key) != tuple:
#      key = (key,)
#    if len(key) != self.dim:
#      raise TypeError(key)
#    elif any([type(k) == slice for k in key]):
#      # slicing N-dimensional data, N ≥ 1
#      indices = []
#      for i, k in enumerate(key):
#        if type(k) == slice:
#          indices.append(self.domain[i].elements[k])
#        else:
#          indices.append((k,))
#      if self.dim == 1:
#        idx = 0
#      else:
#        idx = slice(self.dim)
#      return RETURN([self.value.get(k[idx], NULL) for k in
#        product(*indices)])
#    elif key in self.value:
#      # key directly specifies a single element of the parameter
#      return self.value[key]
#    elif self._valid_key(key):
#      # key is valid, but there's no data
#      return NULL
#    else:
#      # something else went wrong; nothing should be raised here
#      raise KeyError(key)

#  def _valid_key(self, key):
#    """Check that all elements of a __getitem__() key are in the domain."""
#    if self.dim == 0:
#      return False
#    return all([(key[i] in self.domain[i].elements) for i in range(self.dim)])

# GAMS variables are currently functionally equivalent to parameters
Variable = Parameter
