# Copyright (C) 2021 UK Centre for Ecology and Hydrology
from setuptools import setup, find_packages
import json


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


def read_authors(filename):
    authors = []
    with open(filename, 'r') as fz:
        meta = json.load(fz)
        for author in meta['creators']:
            name = author['name'].strip()
            authors.append(name)

    return ', '.join(authors)


setup(
    name='cm4twc',

    version=__version__,

    description='Community Model for the Terrestrial Water Cycle',
    long_description=long_desc,
    long_description_content_type="text/x-rst",

    download_url="https://pypi.python.org/pypi/cm4twc",
    project_urls={
        'Bug Tracker': 'https://github.com/hydro-jules/cm4twc/issues',
        'User Support': 'https://github.com/hydro-jules/cm4twc/discussions',
        'Documentation': 'https://hydro-jules.github.io/cm4twc',
        'Source Code': 'https://github.com/hydro-jules/cm4twc',
    },

    author=read_authors('.zenodo.json'),

    license='BSD-3',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Natural Language :: English',

        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Hydrology',

        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    packages=find_packages(exclude=["docs*"]),

    install_requires=requirements('requirements.txt'),

    extras_require={
        'docs': requirements('requirements-docs.txt')
    }
)
