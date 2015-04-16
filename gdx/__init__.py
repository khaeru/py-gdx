from itertools import chain, zip_longest

from numpy import nan
from pandas import Index, MultiIndex, Series
from xray import DataArray, Dataset

import gdxcc

from .api import type_str, vartype_str, GDX

# commented: for debugging
# import logging
# from logging import debug, warn
# logging.basicConfig(level=logging.WARNING)


__all__ = [
    'File',
    ]


class File(Dataset):
    """Load the file at *filename* into memory.

    *mode* must be 'r' (writing GDX files is not currently supported). If
    *lazy* is ``True`` (default), then the data for GDX parameters is not
    loaded until each parameter is first accessed.

    """
    def __init__(self, filename='', skip=set(), mode='r', lazy=True):
        """Constructor."""
        Dataset.__init__(self)

        # load the GDX API
        self._api = GDX()
        self._api.open_read(filename)

        v, p = self._api.file_version()
        sc, ec = self._api.system_info()
        self.attrs['version'] = v.strip()
        self.attrs['producer'] = p.strip()
        self.attrs['symbol_count'] = sc
        self.attrs['element_count'] = ec

        self._index = [None for _ in range(sc + 1)]
        self._to_skip = skip
        self._skipped = []
        self._state = {}
        self._alias = {}

        # Read symbols
        for s_num in range(sc + 1):
            self._load_symbol(s_num, lazy)

    def _load_symbol(self, index, lazy=True):
        # Read information about the symbol
        name, dim, type_code = self._api.symbol_info(index)
        n_records, vartype, desc = self._api.symbol_info_x(index)
        self._index[index] = name
        attrs = {
            'index': index,
            'name': name,
            'dim': dim,
            'type_code': type_code,
            'records': n_records,
            'vartype': vartype,
            'description': desc,
            }
        # Common code for sets, parameters and variables
        # Set the type
        type_str_ = type_str[type_code]
        if type_code == gdxcc.GMS_DT_PAR and dim == 0:
            type_str_ = 'scalar'
        try:
            vartype_str_ = vartype_str[vartype]
        except KeyError:
            vartype_str_ = ''
        attrs['type_str'] = '{} {}'.format(vartype_str_, type_str_)

        if name in self._to_skip:
            # debug('Skipping {} as directed.'.format(name))
            return
        # debug('Loading {name}: {dim}-D, {records} records, '
        #       '"{description}"'.format(**attrs))

        # Equations and aliases require limited processing
        if type_code == gdxcc.GMS_DT_EQU:
            # warn('Loading of GMS_DT_EQU not implemented: {} {} not loaded.'.
            #      format(index, name))
            return
        elif type_code == gdxcc.GMS_DT_ALIAS:
            parent = self[desc.replace('Aliased with ', '')]
            self._alias[name] = parent.name
            if parent.attrs['_gdx_type_code'] == gdxcc.GMS_DT_SET:
                new_var = parent.copy()
                new_var.name = name
                Dataset.merge(self, {name: new_var}, inplace=True)
                Dataset.set_coords(self, name, inplace=True)
            else:
                raise NotImplementedError('Cannot handle aliases of symbols '
                                          'except GMS_DT_SET: {} {} not loaded'
                                          .format(index, name))
            return

        # Read the domain of the set, as a list of names
        try:
            domain = self._api.symbol_get_domain_x(index)
        except Exception:
            assert name == '*'
            domain = []
        attrs['domain'] = domain

        # Read the elements of the domain directly.
        n_records2 = self._api.data_read_str_start(index)
        assert n_records == n_records2, \
            ('{}: gdxSymbolInfoX ({}) and gdxDataReadStrStart ({}) disagree on'
             ' number of records.').format(name, n_records, n_records2)

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
                # The value is a sequence, containing the level, marginal,
                # lower & upper bounds, etc. Store only the value (first
                # element).
                data[key] = value[gdxcc.GMS_VAL_LEVEL]
        except Exception:
            if len(data) == n_records:
                pass
            else:
                raise

        # Domain as a list of references
        domain_ = [None for _junk in range(dim)] if index > 0 else []
        # If domain is specified for the symbol, try to use that information
        for i, d in enumerate(domain):
            domain_[i] = self[d]
            if d != '*' or len(elements[i]) == 0:
                assert set(domain_[i].values).issuperset(elements[i])
                continue
            # Compute the domain directly for this dimension
            for s in self.coords.values():
                if s.ndim == 1 and set(s.values).issuperset(elements[i]) and \
                        len(s) < len(domain_[i]):
                    domain_[i] = s

        domain = [d.name for d in domain_]
        attrs['domain_inferred'] = domain
        # debug('domain: {}'.format(domain))

        self._state[name] = {
            'attrs': attrs,
            'data': data,
            'domain': domain,
            'elements': elements,
            }

        if type_code == gdxcc.GMS_DT_SET or not lazy:
            self._add_symbol(name)

    def _add_symbol(self, name):
        attrs = self._state[name]['attrs']
        dim = self._state[name]['attrs']['dim']
        data = self._state[name]['data']
        domain = self._state[name]['domain']
        elements = self._state[name]['elements']

        # Continue loading
        if dim == 0:
            new_var = data.popitem()
        elif attrs['type_code'] == gdxcc.GMS_DT_SET and dim == 1:
            new_var = elements[0]
        else:
            try:
                new_var = self._to_dataarray(domain, elements, data,
                                             attrs['type_code'])
            except MemoryError:
                self._state[name] = None
                # warn('Skipping {} because of MemoryError'.format(name))
                return

        Dataset.merge(self, {name: new_var}, inplace=True, join='left')

        if attrs['type_code'] == gdxcc.GMS_DT_SET:
            Dataset.set_coords(self, name, inplace=True)

        for k, v in attrs.items():
            self[name].attrs['_gdx_' + k] = v

        self._state[name] = True

    def _to_dataarray(self, domain, elements, data, type_code):
        assert type_code in (gdxcc.GMS_DT_PAR, gdxcc.GMS_DT_SET,
                             gdxcc.GMS_DT_VAR)

        kwargs = {}
        fill = nan

        # To satisfy xray.DataArray.__init__, two dimensions must not have the
        # same name unless they have the same length. Construct a 'fake'
        # universal set.
        pseudo = sum(map(lambda d: d == '*', domain)) > 1
        if pseudo:
            dim = range(len(domain))
            star = set(chain(*[elements[i] for i in dim if domain[i] == '*' and
                               len(elements[i])]))
            elements = [star if domain[i] == '*' else elements[i] for i in dim]
            extra_tuples = [tuple([e if domain[i] == '*' else elements[i][0]
                                   for i in dim]) for e in star]

        if type_code == gdxcc.GMS_DT_SET:
            data = dict(zip_longest(data.keys(), [True], fillvalue=True))
            fill = False
            kwargs['dtype'] = bool

        if len(data) == 0:
            # Dummy data
            key = tuple([self[d].values[0] for d in domain])
            data[key] = fill

        # Construct the index
        if len(domain) == 1:
            idx = Index(data.keys(), name=domain[0])
        elif len(data) == 1:
            idx = MultiIndex.from_tuples([data.keys()], names=domain)
        else:
            tuples = data.keys()
            if pseudo:
                tuples = list(chain(tuples, extra_tuples))
            idx = MultiIndex.from_tuples(tuples, names=domain)

        return DataArray.from_series(Series(data, index=idx, **kwargs))

    def dealias(self, name):
        """Identify the GDX Symbol that *name* refers to, and return the
        corresponding :class:`xray.DataArray`."""
        return self[self._alias[name]] if name in self._alias else self[name]

    def _loaded_and_cached(self, type_code):
        names = set()
        for name, state in self._state.items():
            if state is True:
                tc = self._variables[name].attrs['_gdx_type_code']
            elif isinstance(state, dict):
                tc = state['attrs']['type_code']
            else:
                continue
            if tc == type_code:
                names.add(name)
        return names

    def sets(self):
        """Return a list of all GDX Sets."""
        return self._loaded_and_cached(gdxcc.GMS_DT_SET)

    def parameters(self):
        """Return a list of all GDX Parameters."""
        return self._loaded_and_cached(gdxcc.GMS_DT_PAR)

    def get_symbol_by_index(self, index):
        """Retrieve the GAMS symbol stored at the *index*-th position in the
        :class:`File`."""
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
        except KeyError:
            if isinstance(self._state[key], dict):
                self._add_symbol(key)
                return Dataset.__getitem__(self, key)
            else:
                raise
