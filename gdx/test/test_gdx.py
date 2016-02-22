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
    ('p4', None),
    ])
actual_info = {
    'N sets': 9,
    'N parameters': 4,
    }


def list_cmp(l1, l2):
    return all([i1 == i2 for i1, i2 in zip(l1, l2)])


class TestGDX:
    def test_init(self):
        gdx.GDX()


class TestFile(TestCase):
    def setUp(self):
        self.f = gdx.File(URI)

    def test_init(self):
        gdx.File(URI)
        with self.assertRaises(FileNotFoundError):
            gdx.File('nonexistent.gdx')

    def test_parameters(self):
        params = self.f.parameters()
        assert len(params) == actual_info['N parameters']

    def test_sets(self):
        sets = self.f.sets()
        assert len(sets) == actual_info['N sets'] + 1

    def test_get_symbol(self):
        self.f['s']

    def test_get_symbol_by_index(self):
        for i, name in enumerate(actual.keys()):
            sym = self.f.get_symbol_by_index(i)
            assert sym.name == name
        # Giving too high an index results in IndexError
        with self.assertRaises(IndexError):
            self.f.get_symbol_by_index(i + 1)

    def test_getattr(self):
        for name in actual.keys():
            getattr(self.f, name)
        with self.assertRaises(AttributeError):
            self.f.notasymbolname

    def test_getitem(self):
        for name in actual.keys():
            self.f[name]
        with self.assertRaises(KeyError):
            self.f['notasymbolname']

    def test_extract(self):
        for name in ['p1', 'p2', 'p3', 'p4']:
            self.f.extract(name)
        with self.assertRaises(KeyError):
            self.f.extract('notasymbolname')


class TestSymbol:
    pass


class TestSet(TestCase):
    def setUp(self):
        self.file = gdx.File(URI)
        self.star = self.file['*']

    def test_len(self):
        assert len(self.file.s) == len(actual['s'])
        assert len(self.file.set('s1')) == len(actual['s1'])
        assert len(self.file.set('s2')) == len(actual['s2'])

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
        def domain(name): return self.file[name].attrs['_gdx_domain']
        assert list_cmp(domain('s'), ['*'])
        assert list_cmp(domain('t'), ['*'])
        assert list_cmp(domain('u'), ['*'])
        assert list_cmp(domain('s1'), ['s'])
        assert list_cmp(domain('s2'), ['s'])
        assert list_cmp(domain('s3'), ['s', 't'])
        assert list_cmp(domain('s4'), ['s', 't', 'u'])
