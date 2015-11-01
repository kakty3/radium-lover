from distutils.core import setup
from Cython.Build import cythonize
import numpy


setup(
    name = "Radium Lover",
    ext_modules = cythonize('edit_distance.pyx'),  # accepts a glob pattern
    include_dirs=[numpy.get_include()],
)