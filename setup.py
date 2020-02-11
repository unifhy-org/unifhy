# -*- coding: utf-8 -*-
# Copyright (C) 2020 HydroJULES
from setuptools import setup


with open("README.md", "r") as fh:
    long_desc = fh.read()

with open('cm4twc/version.py') as fv:
    exec(fv.read())

setup(
    name='cm4twc',

    version=__version__,

    description='Community Model for the Terrestrial Water Cycle',
    long_description=long_desc,
    long_description_content_type="text/markdown",

    url='https://github.com/ThibHlln/cm4twc',

    author='HydroJULES Team',
    author_email='https://hydro-jules.org/',

    license='GPLv3',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Natural Language :: English',

        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Hydrology',

        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython'
    ],

    packages=[
        'cm4twc'
    ],

    install_requires=[
        'numpy',
        'cf-python'
    ]
)
