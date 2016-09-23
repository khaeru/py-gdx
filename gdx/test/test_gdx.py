from collections import OrderedDict

import numpy as np
import pytest

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


actual = OrderedDict([
    ('*', None),
    ('pi', 3.14),
    ('s', ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
    ('t', ['r', 'o', 'y', 'g', 'b', 'i', 'v']),
    ('u', ['CA', 'US', 'CN', 'JP']),
    ('s1', ['a', 'b', 'c', 'd']),
    ('s2', ['e', 'f', 'g']),
    ('s3', None),
    ('s4', None),
    ('s5', ['b', 'd', 'f']),
    ('s6', ['b', 'd', 'f']),
    ('s7', None),
    ('p1', None),
    ('p2', None),
    ('p3', None),
    ('p4', None),
    ('p5', None),
    ('p6', None),
    ])
actual_info = {
    'N sets': 12,
    'N parameters': 7,
    }
actual_info['N symbols'] = sum(actual_info.values()) + 1


def list_cmp(l1, l2):
    return all([i1 == i2 for i1, i2 in zip(l1, l2)])


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

    def test_parameters(self, gdxfile):
        params = gdxfile.parameters()
        assert len(params) == actual_info['N parameters']

    def test_sets(self, gdxfile):
        sets = gdxfile.sets()
        assert len(sets) == actual_info['N sets']

    def test_get_symbol(self, gdxfile):
        gdxfile['s']

    def test_get_symbol_by_index(self, gdxfile):
        for i, name in enumerate(actual.keys()):
            sym = gdxfile.get_symbol_by_index(i)
            assert sym.name == name
        # Giving too high an index results in IndexError
        with pytest.raises(IndexError):
            gdxfile.get_symbol_by_index(gdxfile.attrs['symbol_count'] + 1)

    def test_getattr(self, gdxfile):
        for name in actual.keys():
            getattr(gdxfile, name)
        with pytest.raises(AttributeError):
            gdxfile.notasymbolname

    def test_getitem(self, gdxfile):
        for name in actual.keys():
            gdxfile[name]
        with pytest.raises(KeyError):
            gdxfile['notasymbolname']
        with pytest.raises(KeyError):
            gdxfile['e1']

    def test_info1(self, gdxfile):
        assert gdxfile.info('s1').startswith("<xarray.DataArray 's1' (s1: 4)>")

    def test_info2(self, rawgdx):
        # Use a File where p1 is guaranteed to not have been loaded:
        assert (gdx.File(rawgdx).info('p1') == 'unknown parameter p1(s) — 1 '
                'records: Example parameter with animal data')

    def test_dealias(self, gdxfile):
        assert gdxfile.dealias('s_').equals(gdxfile['s'])

    def test_extract(self, gdxfile, gdxfile_explicit):
        for name in ['p1', 'p2', 'p3', 'p4']:
            gdxfile.extract(name)
        gdxfile_explicit.extract('p5')
        with pytest.raises(KeyError):
            gdxfile.extract('notasymbolname')

    def test_implicit(self, gdxfile):
        assert gdxfile['p6'].shape == (3, 3)


def test_implicit(gdxfile_explicit):
    N = len(gdxfile_explicit['*'])
    assert gdxfile_explicit['p6'].shape == (N, N)


class TestSet:
    def test_len(self, gdxfile):
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

    def test_iter(self, gdxfile):
        for i, elem in enumerate(gdxfile.s):
            assert actual['s'][i] == elem

    def test_domain(self, gdxfile):
        def domain(name): return gdxfile[name].attrs['_gdx_domain']
        assert list_cmp(domain('s'), ['*'])
        assert list_cmp(domain('t'), ['*'])
        assert list_cmp(domain('u'), ['*'])
        assert list_cmp(domain('s1'), ['s'])
        assert list_cmp(domain('s2'), ['s'])
        assert list_cmp(domain('s3'), ['s', 't'])
        assert list_cmp(domain('s4'), ['s', 't', 'u'])
