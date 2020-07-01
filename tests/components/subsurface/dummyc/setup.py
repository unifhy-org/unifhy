from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy as np

ext = Extension(name='dummyc',
                sources=['dummyc.pyx', 'dummy.c'])

setup(
    ext_modules=cythonize(ext),
    include_dirs=[np.get_include()]
)
