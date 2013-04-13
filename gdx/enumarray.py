import numpy

__all__ = ['enumarray']

class enumarray:
  def __init__(self, indices, data=None):
    shape = [len(i) for i in indices]
    if data is None:
      data = numpy.NaN * numpy.ones(shape)
    elif len(shape) != len(data.shape):
        raise ValueError('mismatch of {}-D indice and {}-D data'.format(
          len(shape), len(data.shape)))
    else:
      for i in range(len(shape)):
        if len(indices[i]) != data.shape[i]:
          raise ValueError(
            'dimension {} has index length {} but data length {}'.format(len(
            indices[i]), data.shape[i]))
    self._data = data
    self.dim = len(self._data.shape)
    # use list() to accommodate gdx.Set and other iterables that don't support
    # .index()
    self.indices = [list(i) for i in indices]

  def _indices(self, key):
    """Return a set of indices which can be used to address a NumPy array."""
    try:
      self._data[key]
      return key
    except (ValueError, IndexError):
      if self.dim == 1 and type(key) == str:
        # wrap a string key so len() below doesn't give its length
        key = (key,)
      if len(key) != self.dim:
        raise KeyError('Expected {} dimension(s), got {}: {}'.format(self.dim,
          len(key), key))
      result = []
      for i, k in enumerate(key):
        if type(k) == slice:
          if k == slice(None):
            result.append(k)
          else:
            result.append(range(*k.indices(self._data.shape[i])))
        else:
          if k in self.indices[i]:
            k = (k,)
          # allow a ValueError here to propagate
          result.append([self.indices[i].index(k_) for k_ in k])
      return result

  def __getitem__(self, key):
    try:
      return self._data[self._indices(key)]
    except ValueError:
      print(self._data, self._data.shape, key, self._indices(key))
      assert False

  def __setitem__(self, key, value):
    self._data[self._indices(key)] = value
