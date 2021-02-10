# Copyright (C) 2021 UK Centre for Ecology and Hydrology
from setuptools import setup, find_packages


with open("README.rst", 'r') as fh:
    long_desc = fh.read()

with open("cm4twc/version.py", 'r') as fv:
    exec(fv.read())


def requirements(filename):
    requires = []
    with open(filename, 'r') as fr:
        for line in fr:
            package = line.strip()
            if package:
                requires.append(package)

    return requires


setup(
    name='cm4twc',

    version=__version__,

    description='Community Model for the Terrestrial Water Cycle',
    long_description=long_desc,
    long_description_content_type="text/x-rst",

    url='https://github.com/hydro-jules/cm4twc',

    author='Thibault Hallouin',
    author_email='thibault.hallouin@ncas.ac.uk',

    license='BSD-3',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Natural Language :: English',

        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Hydrology',

        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython'
    ],

    packages=find_packages(exclude=["docs*"]),

    install_requires=requirements('requirements.txt'),

    extras_require={
        'docs': requirements('requirements-docs.txt')
    }
)
