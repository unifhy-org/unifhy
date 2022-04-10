# Copyright (C) 2021 UK Centre for Ecology and Hydrology
from setuptools import setup, find_packages
import json


with open("README.rst", 'r') as fh:
    long_desc = fh.read()

with open("unifhy/version.py", 'r') as fv:
    exec(fv.read())


def read_requirements(filename):
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
    name='unifhy',
    version=__version__,
    description='Unified Framework for Hydrology',
    long_description=long_desc,
    long_description_content_type="text/x-rst",
    download_url="https://pypi.python.org/pypi/unifhy",
    project_urls={
        'Bug Tracker': 'https://github.com/unifhy-org/unifhy/issues',
        'User Support': 'https://github.com/unifhy-org/unifhy/discussions',
        'Documentation': 'https://unifhy-org.github.io/unifhy',
        'Source Code': 'https://github.com/unifhy-org/unifhy',
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
        'Programming Language :: Python'
    ],
    packages=find_packages(exclude=["data*", "docs*", "tests*"]),
    python_requires=">=3.7",
    install_requires=read_requirements('requirements.txt'),
    extras_require={
        'docs': read_requirements('requirements-docs.txt'),
        'tests': read_requirements('requirements-tests.txt')
    }
)
