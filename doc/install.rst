Installation
============

pyGDX depends on the low-level application programming interface (API) provided with GAMS, that allows Python code to access the contents of GDX files.

All platforms
-------------

1. Install the latest version of `GAMS`_.

The remaining steps depend on the platform:

Linux, Mac OS X
---------------

.. note:

   It is fairly painless to install either 'plain' Python or Anaconda on each of Linux and Mac OS X. If you are using Anaconda, be sure to activate an appropriate environment configured with Python 3 before continuing, and remember that you will need to install pyGDX in each new environment where you want to use it.

2. Navigate to the GAMS Python API directory. If gams is installed at (for instance) */opt/gams*, this will be */opt/gams/apifiles/Python/api_34*.

3. Run either ``python setup.py install`` (to install all the GAMS bindings) or ``python gdxsetup.py install`` (to install only the GDX bindings needed by pyGDX).

4. Navigate to the directory containing pyGDX, and again run ``python setup.py install``

Windows
-------

.. note::

   There are multiple ways to get a working pyGDX on Windows, but the following is the simplest for new users.

2. Install `Anaconda`_ for Python 3.5. Install into your home directory (e.g. *C:\\Users\\Yourname\\Anaconda*) instead of the system-wide install—this avoids later issues with permissions.

3. Create a new Anaconda environment using Python 3.4:[#]_ open a Command Prompt and run ``conda create --name py34 python=3.4 anaconda xarray [PACKAGES]``, where ``[PACKAGES]`` are the names of any other packages you may need in this environment. [#]_ Activate the new environment with ``activate py34``.

4. In the same command prompt, navigate to the GAMS Python API directory. If GAMS is installed at (for instance) *C:\\GAMS\\24.6*, this will be *C:\\GAMS\\24.6\\apifiles\\Python\\api_34*. Run either ``python setup.py install`` (to install all the GAMS bindings) or ``python gdxsetup.py install`` (to install only the GDX bindings needed by pyGDX). The bindings will be installed in the *py34* Anaconda environment.

5. Navigate to the directory containing pyGDX, and again run ``python setup.py install``.

Steps 4 and 5 may be repeated for any new Anaconda environment in which pyGDX is needed.


.. [#] This is necessary because GAMS only ships bindings for Python 3.4, and not the newest Python 3.5. Unlike on Mac OS and Linux, the Python 3.4 bindings do not work with Python 3.5.
.. [#] The Anaconda documentation `recommends`_ adding packages when creating the environment, if possible, instead of installing them later.
.. _`GAMS`: https:\\www.gams.com\download\
.. _`Anaconda`: https:\\www.continuum.io\downloads#_windows
.. _`recommends`: http://conda.pydata.org/docs/using/envs.html#create-a-separate-environment
