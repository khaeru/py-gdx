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


def test_import():
    import gdx as gdx_


class TestGDX:
    def test_init(self):
        gdx.GDX()


class TestFile(TestCase):
    def test_init(self):
        f = gdx.File(URI)
        with self.assertRaises(FileNotFoundError):
            f = gdx.File('nonexistent.gdx')

    def test_parameters(self):
        f = gdx.File(URI)
        params = f.parameters()
        assert len(params) == actual_info['N parameters']
        assert all(map(lambda s: isinstance(s, gdx.Parameter), params))

    def test_sets(self):
        f = gdx.File(URI)
        sets = f.sets()
        assert len(sets) == actual_info['N sets']
        assert all(map(lambda s: isinstance(s, gdx.Set), sets))

    def test_get_symbol(self):
        f = gdx.File(URI)
        s = f.get_symbol('s')
        assert isinstance(s, gdx.Set)

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
            sym = getattr(f, name)
        with self.assertRaises(AttributeError):
            sym = f.notasymbolname

    def test_getitem(self):
        f = gdx.File(URI)
        for name in actual.keys():
            sym = f[name]
        with self.assertRaises(KeyError):
            sym = f['notasymbolname']


class TestSymbol:
    pass


class TestSet(TestCase):
    @classmethod
    def setUpClass(self):
        self.file = gdx.File(URI, lazy=True)
        self.star = self.file.get_symbol('*')

    def test_depth(self):
        assert self.star.depth == 0, self.star.depth
        assert self.file.s.depth == 1, self.file.s.depth
        assert self.file.s1.depth == 2, self.file.s1.depth

    def test_len(self):
        assert len(self.file.s) == len(actual['s'])
        assert len(self.file.s1) == len(actual['s1'])
        assert len(self.file.s2) == len(actual['s2'])

    def test_getitem(self):
        for i in range(len(self.file.s)):
            elem = self.file.s[i]
        with self.assertRaises(IndexError):
            elem = self.file.s[i + 1]

    def test_index(self):
        assert self.file.s.get_loc('d') == 3

    def test_iter(self):
        for i, elem in enumerate(self.file.s):
            assert actual['s'][i] == elem

    def test_pandas(self):
        assert self.file.s.domain == [self.star]
        assert self.file.t.domain == [self.star]
        assert self.file.u.domain == [self.star]
        assert self.file.s1.domain == [self.file.s]
        assert self.file.s2.domain == [self.file.s]
        assert self.file.s3.domain == [self.file.s, self.file.t]
        assert self.file.s4.domain == [self.file.s, self.file.t, self.file.u]


class TestParameter:
    @classmethod
    def setUpClass(self):
        self.file = gdx.File(URI)

    def test_example(self):
        p1 = self.file.p1


class TestEquation:
    pass
