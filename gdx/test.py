import gdx


def test_set_data_type():
    gdx.set_data_type('plain')
    gdx.set_data_type('numpy')


class TestGDX:
    def test_init(self):
        gdx.GDX()


class TestFile:
    pass


class TestSymbol:
    pass


class TestSet:
    pass


class TestParameter:
    pass


class TestEquation:
    pass
