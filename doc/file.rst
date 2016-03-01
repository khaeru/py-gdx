Accessing data from GDX files
=============================

.. autoclass:: gdx.File
   :members:

   :class:`File` is a subclass of :py:class:`xarray.Dataset`. The GDX data is represented as follows:

   - One-dimensional GDX Sets are stored as xray *coordinates*.
   - GDX Parameters and multi-dimensional GDX Sets are stored as :py:class:`xarray.DataArray` variables within the :py:class:`xarray.Dataset`.
   - Other information and metadata on GDX Symbols is stored as attributes of the :class:`File`, or attributes of individual data variables or coordinates.

   Individual Symbols are thus available in one of three ways:

   1. As dict-like members of the :py:class:`xarray.Dataset`; see the `xarray documentation`_ for further examples.

      >>> from gdx import File
      >>> f = File('example.gdx')
      >>> f['myparam']

   2. As attributes of the :class:`File`:

      >>> f.myparam

   3. Using :func:`get_symbol_by_index`, using the numerical index of the Symbol within
      the GDX file.

.. _`xarray documentation`: http://xarray.pydata.org/en/stable/data-structures.html#dataset
