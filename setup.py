#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python setup for coverlovin2 package.

Based on sample https://github.com/pypa/sampleproject/blob/master/setup.py
and instructions at
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation
"""

import os

from setuptools import setup
from setuptools import find_packages
from coverlovin2.coverlovin2 import __version__
from coverlovin2.coverlovin2 import __author__
from coverlovin2.coverlovin2 import __url__

# Get the long description from the README.md file
__here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(__here, 'README.md'), encoding='utf-8') as f_:
    long_description = f_.read()

setup(
    name='CoverLovin2',
    version=__version__,
    author=__author__,
    url=__url__,
    description='Recursively parse directories with audio files and download'
                ' album cover art.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Creative Commons Attribution-ShareAlike 3.0 United States License',
    install_requires=[
        'musicbrainzngs == 0.6',
        'mutagen == 1.42.0',
    ],
    # see https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        # XXX: as of 2019/02/07, the Apache-2.0 License is an OSI approved
        #      license: https://opensource.org/licenses/alphabetical
        #      However the listed classifier string is not listed at
        #      https://pypi.org/classifiers/
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Multimedia :: Sound/Audio'
    ],
    keywords='audio image music',
    python_requires='>=3.7',
    # XXX: should Pipfile* also be distributed???
    packages=find_packages(
        exclude=[
            'coverlovin2/test/',
            #'Pipfile',
            #'Pipfile.lock'
            # the following should match .gitignore
            #'.idea/',
            #'.vscode/',
            #'.mypy_cache/',
            #'.pytest_cache/',
            #'build/',
            #'dist/',
            #'CoverLovin2.egg-info/',
            #'htmlcov/',
            #'.coverage',
            #'coverage.xml',
            #'Notes.md',
            ],
        include=[
            'coverlovin2/'
        ]),
    scripts=['coverlovin2/coverlovin2.py'],
    # TODO: does this need work?
    entry_points={
        'console_scripts': [
            'coverlovin2=coverlovin2:main',
            #'coverlovin2=coverlovin2.coverlovin2:main',
        ],
    },
    project_urls={  # Optional
        'Source': __url__,
        'Bug Reports': 'https://github.com/jtmoon79/coverlovin2/issues',
        'Say Thanks!': 'http://saythanks.io/to/coverlovin2',
    },
)
