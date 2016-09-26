import numpy as np
import pytest
import xarray as xr

import gdx
from gdx.pycompat import FileNotFoundError


@pytest.fixture(scope='session')
def rawgdx(request):
    """ Return the path to a GDX file for running tests.

    Invoking this fixture causes the file data/tests.gms to be processed to
    data/tests.gdx. When the fixture is finalized (torn down), the GDX file
    is deleted.

    """
    import os
    import subprocess
    os.chdir('data')
    args = ['gams', 'tests.gms']
    try:  # Python 3.5 and later
        subprocess.run(args)
    except AttributeError:  # Python 3.4 and earlier
        subprocess.call(args)
    os.remove('tests.lst')
    os.chdir('..')

    def finalize():
        os.remove('data/tests.gdx')
    request.addfinalizer(finalize)
    return 'data/tests.gdx'


@pytest.fixture(scope='class')
def gdxfile(rawgdx):
    """A gdx.File fixture."""
    return gdx.File(rawgdx)


@pytest.fixture(scope='class')
def gdxfile_explicit(rawgdx):
    """A gdx.File fixture, instantiated with implicit=False."""
    return gdx.File(rawgdx, implicit=False)


@pytest.fixture(scope='session')
def actual():
    """Return an xarray.Dataset with actual data.

    The returned Dataset has the contents expected when tests.gms is compiled
    to tests.gdx and loaded using gdx.File.
    """

    # Sets, in the order expected in the GDX file
    s = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    t = ['b', 'g', 'r', 'o', 'y', 'i', 'v']
    u = ['CA', 'US', 'CN', 'JP']
    star = s + t[2:] + u

    # Create the dataset
    ds = xr.Dataset({
        'p1': ('s', np.full(len(s), np.nan)),
        'p2': ('t', np.full(len(t), 0.1)),
        'p3': (['s', 't'], np.full([len(s), len(t)], np.nan)),
        'p5': ('*', np.full(len(star), np.nan)),
        },
        coords={
        's': s,
        't': t,
        'u': u,
        '*': star,
        's1': ['a', 'b', 'c', 'd'],
        's2': ['e', 'f', 'g'],
        's3': [],
        's4': [],
        's5': ['b', 'd', 'f'],
        's6': ['b', 'd', 'f'],
        's7': [],
        's_': s,
        })

    # Contents of parameters
    ds['pi'] = 3.14
    ds['p1'].loc['a'] = 1
    ds['p3'].loc[:, 'y'] = 1
    ds['p4'] = (['s1'], np.ones(ds['s1'].size))
    ds['p6'] = (['s', 's1', 't'],
                np.full([len(s), ds['s1'].size, len(t)], np.nan))

    ds['p7'] = (['*', '*'],
                np.full([ds['*'].size] * 2, np.nan))
    ds['p7'].loc['a', 'o'] = 1
    ds['p7'].loc['r', 'US'] = 2
    ds['p7'].loc['CA', 'b'] = 3

    # Set the _gdx_index attribute on each variable
    order = ['*', 'pi', 's', 't', 'u', 's1', 's2', 's3', 's4', 's5', 's6',
             's7', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'e1', 'v1', 'v2',
             's_', ]
    for num, name in enumerate(order):
        try:
            ds[name].attrs['_gdx_index'] = num
        except KeyError:
            # These names do not appear in the loaded gdx.File object
            assert name in ['e1', 'v1', 'v2']

    return ds


def test_implicit(gdxfile_explicit):
    N = len(gdxfile_explicit['*'])
    assert gdxfile_explicit['p7'].shape == (N, N)


class TestAPI:
    def test_gdx(self):
        gdx.GDX()

    def test_bad_method(self):
        api = gdx.GDX()
        with pytest.raises(NotImplementedError):
            api.call('NotAMethod')
        with pytest.raises(AttributeError):
            api.not_a_method()


class TestFile:
    def test_init(self, rawgdx):
        gdx.File(rawgdx)
        gdx.File(rawgdx, lazy=False)
        with pytest.raises(FileNotFoundError):
            gdx.File('nonexistent.gdx')

    def test_num_parameters(self, gdxfile, actual):
        print(gdxfile.parameters())
        assert len(gdxfile.parameters()) == len(actual.data_vars)

    def test_num_sets(self, gdxfile, actual):
        assert len(gdxfile.sets()) == len(actual.coords)

    def test_get_symbol(self, gdxfile):
        gdxfile['s']

    def test_get_symbol_by_index(self, gdxfile, actual):
        for name in actual:
            sym = gdxfile.get_symbol_by_index(actual[name].attrs['_gdx_index'])
            assert sym.name == name
        # Giving too high an index results in IndexError
        with pytest.raises(IndexError):
            gdxfile.get_symbol_by_index(gdxfile.attrs['symbol_count'] + 1)

    def test_getattr(self, gdxfile, actual):
        for name in actual:
            getattr(gdxfile, name)
        with pytest.raises(AttributeError):
            gdxfile.notasymbolname

    def test_getitem(self, gdxfile, actual):
        for name in actual:
            gdxfile[name]
        with pytest.raises(KeyError):
            gdxfile['notasymbolname']
        with pytest.raises(KeyError):
            gdxfile['e1']

    def test_info1(self, gdxfile):
        assert gdxfile.info('s1').startswith("<xarray.DataArray 's1' (s1: 4)>")

    def test_info2(self, rawgdx):
        # Use a File where p1 is guaranteed to not have been loaded:
        assert (gdx.File(rawgdx).info('p1') == 'unknown parameter p1(s), 1 '
                'records: Example parameter with animal data')

    def test_dealias(self, gdxfile):
        assert gdxfile.dealias('s_').equals(gdxfile['s'])

    def test_domain(self, gdxfile, actual):
        assert gdxfile['p6'].dims == actual['p6'].dims

    def test_extract(self, gdxfile, gdxfile_explicit, actual):
        # TODO add p5, p7
        for name in ['p1', 'p2', 'p3', 'p4', 'p6']:
            assert gdxfile.extract(name).equals(actual[name])

        gdxfile_explicit.extract('p5')

        with pytest.raises(KeyError):
            gdxfile.extract('notasymbolname')

    def test_implicit(self, gdxfile):
        assert gdxfile['p7'].shape == (3, 3)


class TestSet:
    def test_len(self, gdxfile, actual):
        assert len(gdxfile.s) == len(actual['s'])
        assert len(gdxfile.set('s1')) == len(actual['s1'])
        assert len(gdxfile.set('s2')) == len(actual['s2'])

    def test_getitem(self, gdxfile):
        for i in range(len(gdxfile.s)):
            gdxfile.s[i]
        with pytest.raises(IndexError):
            gdxfile.s[i + 1]

    def test_index(self, gdxfile):
            assert np.argwhere(gdxfile.s.values == 'd') == 3

    def test_iter(self, gdxfile, actual):
        for i, elem in enumerate(gdxfile.s):
            assert actual['s'][i] == elem

    def test_domain(self, gdxfile):
        def domain(name):
            return gdxfile[name].attrs['_gdx_domain']

        def list_cmp(l1, l2):
            return all([i1 == i2 for i1, i2 in zip(l1, l2)])

        assert list_cmp(domain('s'), ['*'])
        assert list_cmp(domain('t'), ['*'])
        assert list_cmp(domain('u'), ['*'])
        assert list_cmp(domain('s1'), ['s'])
        assert list_cmp(domain('s2'), ['s'])
        assert list_cmp(domain('s3'), ['s', 't'])
        assert list_cmp(domain('s4'), ['s', 't', 'u'])
