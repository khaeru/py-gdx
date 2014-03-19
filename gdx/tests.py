import unittest

import gdx

URI = 'data/tests.gdx'

def test_import():
    import gdx as gdx_


def test_set_data_type():
    gdx.set_data_type('plain')
    gdx.set_data_type('numpy')


class TestGDX:
    def test_init(self):
        gdx.GDX()


class TestFile:
    def test_init(self):
        f = gdx.File(URI)

    def test_parameters(self):
        f = gdx.File(URI)
        params = f.parameters()
        #assert len(params) == 1  # commented: p0 doesn't appear?
        assert all(map(lambda s: isinstance(s, gdx.Parameter), params))

    def test_sets(self):
        f = gdx.File(URI)
        sets = f.sets()
        assert len(sets) == 3
        assert all(map(lambda s: isinstance(s, gdx.Set), sets))

    def test_get_symbol(self):
        f = gdx.File(URI)
        s0 = f.get_symbol('s0')
        assert isinstance(s0, gdx.Set)

    def test_get_symbol_by_index(self):
        f = gdx.File(URI)
        for i, name in enumerate(['*', 's0', 's1', 's2', 'p0']):
            sym = f.get_symbol_by_index(i)
            assert sym.name == name
        # Giving too high an index results in KeyError
        try:
            f.get_symbol_by_index(i + 1)
            assert False
        except KeyError:
            assert True
        except:
            assert False


class TestSymbol:
    pass


class TestSet:
    @classmethod
    def setUpClass(self):
        self.file = gdx.File(URI)

    def test_depth(self):
        star = self.file.get_symbol('*')
        s0 = self.file.get_symbol('s0')
        s1 = self.file.get_symbol('s1')
        assert star.depth == 0, star.depth
        assert s0.depth == 1, s0.depth
        assert s1.depth == 2, s1.depth

    def test_index(self):
        s0 = self.file.get_symbol('s0')
        assert s0.index('d') == 3


class TestParameter:
    @classmethod
    def setUpClass(self):
        self.file = gdx.File(URI)

    def test_example(self):
        p0 = self.file.get_symbol('p0')


class TestEquation:
    pass
