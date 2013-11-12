import numpy

__all__ = ['enumarray']


class enumarray:
    def __init__(self, labels, data=None):
        """An enumerated NumPy array.

        Create an enumarray with the given *labels*, which must be specified as
        an iterable of iterables. If *data* is supplied (optional), it forms
        the values in the enumarray; otherwise the enumarray is filled with
        numpy.NaN.

        The enumarray can be addressed in a variety of ways:

        The *labels* are converted to `list`s, so care should be taken when
        passing iterable but unordered types (`dict`, `set`) containing labels.
        Any type of label object (i.e. not only `str`) is accepted; but
        ambiguous behaviour may result for:

        - Integer labels that are also within the range of a particular
          dimension.
        - Labels that are slices.

        The *data* is converted using `numpy.asarray`, so no copy is performed
        if it is already an ndarray.
        """
        # determine the shape of the enumarray from the labels
        shape = []
        for i in labels:
            shape.append(len(i))
            if shape[-1] != len(set(i)):  # check that elements are unique
                raise TypeError(('dimension {} has duplicate labels among {}'
                                 ).format(len(shape) + 1, i))
        # process the data, if any
        if data is None:  # no data supplied
            data = numpy.NaN * numpy.ones(shape)
        else:
            data = numpy.asarray(data)
            if len(shape) != len(data.shape):  # check that data & labels agree
                raise ValueError(('mismatch of {}-D labels and {}-D data'
                                  ).format(len(shape), len(data.shape)))
            for i in range(len(shape)):  # check each dim. of data and label
                if len(labels[i]) != data.shape[i]:
                    raise ValueError(('dimension {} has {} labels but length '
                                      '{}').format(len(labels[i]),
                                     data.shape[i]))
        # store the data, dimension, and convert lable iterables to lists
        self._data = data
        self.dim = len(self._data.shape)
        self.labels = [list(i) for i in labels]

    def _indices(self, key):
        """Return a set of indices which can be used to address a NumPy array.

        For any *key* object or tuple, return a tuple of integer indices to the
        NumPy array enumarray._data.
        """
        try:  # try to use the key directly
            # TODO this can be expensive if *key* is standard, but expensive,
            #      NumPy way of indexing arrays. Streamline if possible.
            self._data[key]
            return key
        except (ValueError, IndexError):  # key contains at least some labels
            pass
        # wrap a string key to a 1-D array so len() below doesn't give the
        # length of the string
        # TODO check if this works without the typecheck
        if self.dim == 1 and type(key) == str:
            key = (key,)
        if len(key) != self.dim:  # check that the key is of proper length
            raise KeyError('expected {} dimension(s), got {}: {}'.format(
                self.dim, len(key), key))
        # interpret key contents, dimension by dimension
        result = []
        for i, k in enumerate(key):  # i is dimension, k is key contents
            if type(k) == slice:  # slice objects
                if k == slice(None):  # an 'all' slice (ie. ":") passes through
                    result.append(k)
                else:  # convert all other slices to indices
                    result.append(range(*k.indices(self._data.shape[i])))
            elif isinstance(k, int):  # integers: use directly as single index
                result.append(k)
            else:  # other contents
                try:
                    result.append(self.labels[i].index(k))
                    continue
                except ValueError:
                    pass
                if isinstance(k, type(self.labels[i][0])):
                    # key is of same type as the labels for this dimension, so
                    # it is probably a single label
                    k = (k,)
                # look up elements of k (may only be 1) in the list of labels
                # for this dimension
                _result = []
                try:
                    for k_ in k:
                        _result.append(self.labels[i].index(k_))
                except ValueError:  # one of the labels was incorrect
                    raise ValueError(
                        ("label '{}' in slice/index {} does not appear in "
                         "dimension {}: {}").format(k_, k, i, self.labels[i]))\
                        from None
                result.append(_result)
        return tuple(result)

    def __getitem__(self, key):
        try:
            return self._data[self._indices(key)]
        except ValueError as e:
            print(self._data, self._data.shape, key, self._indices(key))
            raise e

    def __setitem__(self, key, value):
        self._data[self._indices(key)] = value

    def __str__(self):
        # TODO add pretty-printing
        return str(self._data)

if __name__ == '__main__':
    ea = enumarray(labels=(('a', 'b', 'c'), ('d', 'e')),
                   data=numpy.arange(6).reshape((3, 2)))
    print(ea)
    print(ea['b', :])
    print(ea[('a', 'c'), -1])
    print(ea[:, 'e'])
