GDX file data access
====================

pyGDX is a Python package for accessing data stored in *GAMS Data eXchange* (GDX) files. GDX is a proprietary, binary file format used by the General Algebraic Modelling System (GAMS_); pyGDX uses the Python bindings for the `GDX API`_.

pyGDX uses xarray_ to provide labeled, multidimensional data structures for accessing data. A :class:`gdx.File` is a thinly-wrapped :py:class:`xarray.Dataset`.

Report bugs, suggest feature ideas or view the source code on `GitHub`_.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   install
   gdx
   file
   api

License
-------

PyGDX is provided under the `MIT license`_.

History
-------

PyGDX was inspired by the similar package, also named `py-gdx, by Geoff Leyland`_.

.. Indices and tables
   ==================
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

.. _`MIT license`: https://github.com/khaeru/py-gdx/blob/master/LICENSE
.. _GAMS: http://www.gams.com
.. _`GDX API`: http://www.gams.com/dd/docs/api/expert-level/gdxqdrep.html
.. _`Github`: http://github.com/khaeru/py-gdx
.. _xarray: http://xarray.pydata.org
.. _`py-gdx, by Geoff Leyland`: https://github.com/geoffleyland/py-gdx
