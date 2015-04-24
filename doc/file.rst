gdx.File
========

.. autoclass:: gdx.File
   :members:

   :class:`File` is a subclass of :class:`xray.Dataset`. The GDX data is
   represented as follows:

   - One-dimensional GDX Sets are stored as xray *coordinates*.
   - GDX Parameters and multi-dimensional GDX Sets are stored as
     :class:`xray.DataArray` variables within the :class:`xray.Dataset`.
   - Other information and metadata on GDX Symbols is stored as attributes of
     the :class:`File`, or attributes of individual data variables or
     coordinates.

   Individual Symbols are thus available in one of three ways:

   1. As dict-like members of the :class:`xray.Dataset`; see
      http://xray.readthedocs.org/en/stable/data-structures.html#dataset:

      >>> f = File('example.gdx')
      >>> f['myparam']

   2. As attributes of the :class:`File`:

      >>> f.myparam

   3. Using :func:`get_symbol_by_index`, using the index of the Symbol within
      the GDX file.
