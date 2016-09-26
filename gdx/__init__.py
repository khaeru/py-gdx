# coding: utf-8
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from itertools import cycle
from logging import debug, info
# commented: for debugging
# import logging
# logging.basicConfig(level=logging.DEBUG)

import numpy
import pandas
import xarray as xr

from .pycompat import install_aliases, filter, raise_from, range, super, zip
install_aliases()

from .api import GDX, gdxcc, type_str, vartype_str


__version__ = '2'


__all__ = [
    'File',
    ]


class File(xr.Dataset):
    """Load the file at *filename* into memory.

    If *lazy* is ``True`` (default), then the data for GDX Parameters is not
    loaded until each individual parameter is first accessed; otherwise all
    parameters except those listed in *skip* (default: empty) are loaded
    immediately.

    If *implicit* is ``True`` (default) then, for each dimension of any GDX
    Parameter declared over '*' (the universal set), an implicit set is
    constructed, containing only the labels appearing in the respective
    dimension of that parameter.

    .. note::

       For instance, the GAMS Parameter ``foo(*,*,*)`` is loaded as
       ``foo(_foo_0,_foo_1,_foo_2)``, where ``_foo_0`` is an implicit set that
       contains only labels appearing along the first dimension of ``foo``,
       etc. This workaround is essential for GDX files where ``*`` is large;
       otherwise, loading ``foo`` as declared raises :py:class:`MemoryError`.

    """
    # For the benefit of xr.Dataset.__getattr__
    _api = None
    _index = []
    _state = {}
    _alias = {}
    _implicit = False

    def __init__(self, filename='', lazy=True, implicit=True, skip=set()):
        """Constructor."""
        super(File, self).__init__()  # Invoke Dataset constructor

        # load the GDX API
        self._api = GDX()
        self._api.open_read(str(filename))

        # Basic information about the GDX file
        v, p = self._api.file_version()
        sc, ec = self._api.system_info()
        self.attrs['version'] = v.strip()
        self.attrs['producer'] = p.strip()
        self.attrs['symbol_count'] = sc
        self.attrs['element_count'] = ec

        # Initialize private variables
        self._index = [None for _ in range(sc + 1)]
        self._state = {}
        self._alias = {}
        self._implicit = implicit

        # Read symbols
        for s_num in range(sc + 1):
            name, type_code = self._load_symbol(s_num)
            if type_code == gdxcc.GMS_DT_SET and name not in skip:
                self._load_symbol_data(name)

        if not lazy:
            for name in filter(None, self._index):
                if name not in skip:
                    self._load_symbol_data(name)

    def _load_symbol(self, index):
        """Load the *index*-th Symbol in the GDX file."""
        # Load basic information
        name, dim, type_code = self._api.symbol_info(index)
        n_records, vartype, desc = self._api.symbol_info_x(index)

        self._index[index] = name  # Record the name

        attrs = {
            'index': index,
            'name': name,
            'dim': dim,
            'type_code': type_code,
            'records': n_records,
            'vartype': vartype,
            'description': desc,
            }

        # Assemble a string description of the Symbol's type
        type_str_ = type_str[type_code]
        if type_code == gdxcc.GMS_DT_PAR and dim == 0:
            type_str_ = 'scalar'
        try:
            vartype_str_ = vartype_str[vartype]
        except KeyError:  # pragma: no cover
            # Some other vartype is returned that's not described by the GDX
            # API docs
            vartype_str_ = ''
        attrs['type_str'] = '{} {}'.format(vartype_str_, type_str_)

        debug(str('Loading #{index} {name}: {dim}-D, {records} records, '
                  u'"{description}"').format(**attrs))

        # Equations and Aliases require limited processing
        if type_code == gdxcc.GMS_DT_EQU:
            info('Loading of GMS_DT_EQU not implemented: {} {} not loaded.'.
                 format(index, name))
            self._state[name] = None
            return name, type_code
        elif type_code == gdxcc.GMS_DT_ALIAS:
            parent = desc.replace('Aliased with ', '')
            self._alias[name] = parent
            assert self[parent].attrs['_gdx_type_code'] == gdxcc.GMS_DT_SET
            # Duplicate the variable
            self._variables[name] = self._variables[parent]
            self._state[name] = True
            super(File, self).set_coords(name, inplace=True)
            return name, type_code

        # The Symbol is either a Set, Parameter or Variable
        try:  # Read the domain, as a list of names
            domain = self._api.symbol_get_domain_x(index)
            debug('domain: {}'.format(domain))
        except Exception:  # gdxSymbolGetDomainX fails for the universal set
            assert name == '*'
            domain = []

        # Cache the attributes
        attrs['domain'] = domain
        self._state[name] = {'attrs': attrs}

        return name, type_code

    def _load_symbol_data(self, name):
        """Load the Symbol *name*."""
        if self._state[name] in (True, None):  # Skip Symbols already loaded
            return

        # Unpack attributes
        attrs = self._state[name]['attrs']
        index, dim, domain, records = [attrs[k] for k in ('index', 'dim',
                                                          'domain', 'records')]

        # Read the data
        self._cache_data(name, index, dim, records)

        # If the GAMS method 'sameas' is invoked in a program, the resulting
        # GDX file contains an empty Set named 'SameAs' with domain (*,*). Do
        # not read this
        if name == 'SameAs' and domain == ['*', '*']:
            self._state[name] = None
            self._index[index] = None
            return

        domain = self._infer_domain(name, domain,
                                    self._state[name]['elements'])

        # Create an xr.DataArray with the Symbol's data
        self._add_symbol(name, dim, domain, attrs)

    def _cache_data(self, name, index, dim, records):
        """Read data for the Symbol *name* from the GDX file."""
        # Initiate the data read. The API method returns a number of records,
        # which should match that given by gdxSymbolInfoX in _load_symbol()
        records2 = self._api.data_read_str_start(index)
        assert records == records2, \
            ('{}: gdxSymbolInfoX ({}) and gdxDataReadStrStart ({}) disagree on'
             ' number of records.').format(name, records, records2)

        # Indices of data records, one list per dimension
        elements = [list() for _ in range(dim)]
        # Data points. Keys are index tuples, values are data. For a 1-D Set,
        # the data is the GDX 'string number' of the text associated with the
        # element
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
                # The value is a sequence, containing the level, marginal,
                # lower & upper bounds, etc. Store only the value (first
                # element).
                data[key] = value[gdxcc.GMS_VAL_LEVEL]
        except Exception:
            if len(data) == records:
                pass  # All data has been read
            else:  # pragma: no cover
                raise  # Some other read error

        # Cache the read data
        self._state[name].update({
            'data': data,
            'elements': elements,
            })

    def _infer_domain(self, name, domain, elements):
        """Infer the domain of the Symbol *name*.

        Lazy GAMS modellers may create variables like myvar(*,*,*,*). If the
        size of the universal set * is large, then attempting to instantiate a
        xr.DataArray with this many elements may cause a MemoryError. For every
        dimension of *name* defined on the domain '*' this method tries to find
        a Set from the file which contains all the labels appearing in *name*'s
        data.

        """
        if '*' not in domain:
            return domain
        debug('guessing a better domain for {}: {}'.format(name, domain))

        # Domain as a list of references to Variables in the File/xr.Dataset
        domain_ = [self[d] for d in domain]

        for i, d in enumerate(domain_):  # Iterate over dimensions
            e = set(elements[i])
            if d.name != '*' or len(e) == 0:  # pragma: no cover
                assert set(d.values).issuperset(e)
                continue  # The stated domain matches the data; or no data
            # '*' is given
            if (self._state[name]['attrs']['type_code'] == gdxcc.GMS_DT_PAR and
                    self._implicit):
                d = '_{}_{}'.format(name, i)
                debug(('Constructing implicit set {} for dimension {} of {}\n'
                       ' {} instead of {} elements')
                      .format(d, name, i, len(e), len(self['*'])))
                self.coords[d] = elements[i]
                d = self[d]
            else:
                # try to find a smaller domain for this dimension
                # Iterate over every Set/Coordinate
                for s in self.coords.values():
                    if s.ndim == 1 and set(s.values).issuperset(e) and \
                            len(s) < len(d):
                        d = s  # Found a smaller Set; use this instead
            domain_[i] = d

        # Convert the references to names
        inferred = [d.name for d in domain_]

        if domain != inferred:
            # Store the result
            self._state[name]['attrs']['domain_inferred'] = inferred
            debug('…inferred {}.'.format(inferred))
        else:
            debug('…failed.')

        return inferred

    def _root_dim(self, dim):
        """Return the ultimate ancestor of the 1-D Set *dim*."""
        parent = self[dim].dims[0]
        return dim if parent == dim else self._root_dim(parent)

    def _empty(self, *dims, **kwargs):
        """Return an empty numpy.ndarray for a GAMS Set or Parameter."""
        size = []
        dtypes = []
        for d in dims:
            size.append(len(self[d]))
            dtypes.append(self[d].dtype)
        dtype = kwargs.pop('dtype', numpy.result_type(*dtypes))
        fv = kwargs.pop('fill_value')
        return numpy.full(size, fill_value=fv, dtype=dtype)

    def _add_symbol(self, name, dim, domain, attrs):
        """Add a xray.DataArray with the data from Symbol *name*."""
        # Transform the attrs for storage, unpack data
        gdx_attrs = {'_gdx_{}'.format(k): v for k, v in attrs.items()}
        data = self._state[name]['data']
        elements = self._state[name]['elements']

        # Erase the cache; this also prevents __getitem__ from triggering lazy-
        # loading, which is still in progress
        self._state[name] = True

        kwargs = {}  # Arguments to xr.Dataset.__setitem__()
        if dim == 0:
            # 0-D Variable or scalar Parameter
            super(File, self).__setitem__(name, ([], data.popitem()[1],
                                                 gdx_attrs))
            return
        elif attrs['type_code'] == gdxcc.GMS_DT_SET:  # GAMS Set
            if dim == 1:
                # One-dimensional Set
                self.coords[name] = elements[0]
                self.coords[name].attrs = gdx_attrs
            else:
                # Multi-dimensional Sets are mappings indexed by other Sets;
                # elements are either 'on'/True or 'off'/False
                kwargs['dtype'] = bool
                kwargs['fill_value'] = False

                # Don't define over the actual domain dimensions, but over the
                # parent Set/xr.Coordinates for each dimension
                dims = [self._root_dim(d) for d in domain]

                # Update coords
                self.coords.__setitem__(name, (dims, self._empty(*domain,
                                                                 **kwargs),
                                               gdx_attrs))

                # Store the elements
                for k in data.keys():
                    self[name].loc[k] = k if dim == 1 else True
        else:  # 1+-dimensional GAMS Parameters
            kwargs['dtype'] = float
            kwargs['fill_value'] = numpy.nan

            dims = [self._root_dim(d) for d in domain]  # Same as above

            # Create an empty xr.DataArray; this ensures that the data
            # read in below has the proper form and indices
            super(File, self).__setitem__(name, (dims, self._empty(*domain,
                                                                   **kwargs),
                                                 gdx_attrs))

            # Fill in extra keys
            longest = numpy.argmax(self[name].values.shape)
            iters = []
            for i, d in enumerate(dims):
                if i == longest:
                    iters.append(self[d].to_index())
                else:
                    iters.append(cycle(self[d].to_index()))
            data.update({k: numpy.nan for k in set(zip(*iters)) -
                         set(data.keys())})

            # Use pandas and xarray IO methods to convert data, a dict, to a
            # xr.DataArray of the correct shape, then extract its values
            tmp = pandas.Series(data)
            tmp.index.names = dims
            tmp = xr.DataArray.from_series(tmp).reindex_like(self[name])
            self[name].values = tmp.values

    def dealias(self, name):
        """Identify the GDX Symbol that *name* refers to, and return the
        corresponding :py:class:`xarray.DataArray`."""
        return self[self._alias[name]] if name in self._alias else self[name]

    def extract(self, name):
        """Extract the GAMS Symbol *name* from the dataset.

        The Sets and Parameters in the :class:`File` can be accessed directly,
        as e.g. `f['name']`; but for more complex xarray operations, such as
        concatenation and merging, this carries along sub-Sets and other
        Coordinates which confound xarray.

        :func:`extract()` returns a self-contained :py:class:`xarray.DataArray`
        with the declared dimensions of the Symbol (and *only* those
        dimensions), which does not make reference to the :class:`File`.
        """
        # Copy the Symbol, triggering lazy-loading if needed
        result = self[name].copy()

        # Declared dimensions of the Symbol, and their parents
        try:
            domain = result.attrs['_gdx_domain_inferred']
        except KeyError:  # No domain was inferred for this Symbol
            domain = result.attrs['_gdx_domain']
        dims = {c: self._root_dim(c) for c in domain}
        keep = set(dims.keys()) | set(dims.values())

        # Extraneous dimensions
        drop_coords = set(result.coords) - keep

        # Reduce the data
        for c, p in dims.items():
            if c == '*':  # Dimension is '*', drop empty labels
                result = result.dropna(dim='*', how='all')
            elif c == p:  # Dimension already indexed by the correct coord
                continue
            else:
                # Dimension is indexed by 'p', but declared 'c'. First drop
                # the elements which do not appear in the sub-Set c;, then
                # rename 'p' to 'c'
                drop = set(self[p].values) - set(self[c].values) - set('')
                result = result.drop(drop, dim=p).swap_dims({p: c})
                # Add the old coord to the set of coords to drop
                drop_coords.add(p)
        # Do this last, in case two dimensions have the same parent (p)
        return result.drop(drop_coords)

    def info(self, name):
        """Informal string representation of the Symbol with *name*."""
        if isinstance(self._state[name], dict):
            attrs = self._state[name]['attrs']
            return '{} {}({}), {} records: {}'.format(
                attrs['type_str'], name, ','.join(attrs['domain']),
                attrs['records'], attrs['description'])
        else:
            return repr(self[name])

    def _loaded_and_cached(self, type_code):
        """Return a list of loaded and not-loaded Symbols of *type_code*."""
        names = set()
        for name, state in self._state.items():
            if state is True:
                tc = self._variables[name].attrs['_gdx_type_code']
            elif isinstance(state, dict):
                tc = state['attrs']['type_code']
            else:  # pragma: no cover
                continue
            if tc == type_code:
                names.add(name)
        return names

    def set(self, name, as_dict=False):
        """Return the elements of GAMS Set *name*.

        Because :py:mod:`xarray` stores non-null labels for each element of a
        coord, a GAMS sub-Set will contain some ``''`` elements, corresponding
        to elements of the parent Set which do not appear in *name*.
        :func:`set()` returns the elements without these placeholders.

        """
        assert self[name].attrs['_gdx_type_code'] == gdxcc.GMS_DT_SET, \
            'Variable {} is not a GAMS Set'.format(name)
        if len(self[name].dims) > 1:
            return self[name]
        elif as_dict:
            from collections import OrderedDict
            result = OrderedDict()
            parent = self[name].attrs['_gdx_domain'][0]
            for label in self[parent].values:
                result[label] = label in self[name].values
            return result
        else:
            return list(self[name].values)

    def sets(self):
        """Return a list of all GDX Sets."""
        return self._loaded_and_cached(gdxcc.GMS_DT_SET)

    def parameters(self):
        """Return a list of all GDX Parameters."""
        return self._loaded_and_cached(gdxcc.GMS_DT_PAR)

    def get_symbol_by_index(self, index):
        """Retrieve the GAMS Symbol from the *index*-th position of the
        :class:`File`."""
        return self[self._index[index]]

    def __getitem__(self, key):
        """Set element access."""
        try:
            return super(File, self).__getitem__(key)
        except KeyError as e:
            if isinstance(self._state[key], dict):
                debug('Lazy-loading {}'.format(key))
                self._load_symbol_data(key)
                return super(File, self).__getitem__(key)
            else:
                raise raise_from(KeyError(key), e)
