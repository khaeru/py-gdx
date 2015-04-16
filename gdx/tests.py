from collections import OrderedDict
from unittest import TestCase

import numpy as np
import gdx


URI = 'data/tests.gdx'


actual = OrderedDict([
    ('*', None),
    ('s', ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
    ('t', ['r', 'o', 'y', 'g', 'b', 'i', 'v']),
    ('u', ['CA', 'US', 'CN', 'JP']),
    ('s1', ['a', 'b', 'c', 'd']),
    ('s2', ['e', 'f', 'g']),
    ('s3', None),
    ('s4', None),
    ('s5', ['b', 'd', 'f']),
    ('s6', ['b', 'd', 'f']),
    ('p1', None),
    ('p2', None),
    ('p3', None),
    ])
actual_info = {
    'N sets': 9,
    'N parameters': 3,
    }


def list_cmp(l1, l2):
    print(l1, l2)
    return all([i1 == i2 for i1, i2 in zip(l1, l2)])


class TestGDX:
    def test_init(self):
        gdx.GDX()


class TestFile(TestCase):
    def test_init(self):
        gdx.File(URI)
        with self.assertRaises(FileNotFoundError):
            gdx.File('nonexistent.gdx')

    def test_parameters(self):
        f = gdx.File(URI)
        params = f.parameters()
        assert len(params) == actual_info['N parameters']

    def test_sets(self):
        f = gdx.File(URI)
        sets = f.sets()
        assert len(sets) == actual_info['N sets'] + 1

    def test_get_symbol(self):
        f = gdx.File(URI)
        f['s']

    def test_get_symbol_by_index(self):
        f = gdx.File(URI)
        for i, name in enumerate(actual.keys()):
            sym = f.get_symbol_by_index(i)
            assert sym.name == name
        # Giving too high an index results in IndexError
        with self.assertRaises(IndexError):
            f.get_symbol_by_index(i + 1)

    def test_getattr(self):
        f = gdx.File(URI)
        for name in actual.keys():
            getattr(f, name)
        with self.assertRaises(AttributeError):
            f.notasymbolname

    def test_getitem(self):
        f = gdx.File(URI)
        for name in actual.keys():
            f[name]
        with self.assertRaises(KeyError):
            f['notasymbolname']


class TestSymbol:
    pass


class TestSet(TestCase):
    @classmethod
    def setUpClass(self):
        self.file = gdx.File(URI)
        self.star = self.file['*']

    def test_len(self):
        assert len(self.file.s) == len(actual['s'])
        assert len(self.file.s1) == len(actual['s1'])
        assert len(self.file.s2) == len(actual['s2'])

    def test_getitem(self):
        for i in range(len(self.file.s)):
            self.file.s[i]
        with self.assertRaises(IndexError):
            self.file.s[i + 1]

    def test_index(self):
            assert np.argwhere(self.file.s.values == 'd') == 3

    def test_iter(self):
        for i, elem in enumerate(self.file.s):
            assert actual['s'][i] == elem

    def test_domain(self):
        domain = lambda name: self.file[name].attrs['_gdx_domain']
        assert list_cmp(domain('s'), ['*'])
        assert list_cmp(domain('t'), ['*'])
        assert list_cmp(domain('u'), ['*'])
        assert list_cmp(domain('s1'), ['s'])
        assert list_cmp(domain('s2'), ['s'])
        assert list_cmp(domain('s3'), ['s', 't'])
        assert list_cmp(domain('s4'), ['s', 't', 'u'])


class TestParameter:
    @classmethod
    def setUpClass(self):
        self.file = gdx.File(URI)

    def test_example(self):
        self.file.p1


class TestEquation:
    pass
