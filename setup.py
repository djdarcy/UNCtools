#!/usr/bin/env python3

from setuptools import setup, find_packages
import os
import sys
from setuptools import setup, find_packages

# Read the version from unctools/__init__.py
with open('unctools/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip("'\"")
            break
    else:
        version = '0.1.0'

# Read long description from README.md
if os.path.exists('README.md'):
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = 'UNCtools - A comprehensive toolkit for handling UNC paths and network drives'

setup(
    name='unctools',
    version='0.1.0',
    description='A comprehensive toolkit for handling UNC paths, network drives, and substituted drives',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Dustin Darcy',
    author_email='dustindarcy@gmail.com',  # Replace with your email
    url='https://github.com/djdacy/unctools',  # Replace with your repo URL
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: OS Independent',		
        'Topic :: System :: Filesystems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='unc, network, windows, path, file, share, subst, path conversion',
    python_requires='>=3.6',
    install_requires=[
        'pathlib',  # Python 3.4+ already has this in the standard library
    ],
    extras_require={
        'windows': [
            'pywin32>=223',  # For advanced Windows functionality
        ],
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.10.0',
            'flake8>=3.8.0',
            'mypy>=0.800',
            'black>=20.8b1',
            'tox>=3.20.0',
        ],
        'docs': [
            'sphinx>=3.0.0',
            'sphinx-rtd-theme>=0.5.0',
            'myst-parser>=0.15.0',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/djdarcy/unctools/issues',  # Replace with your repo
        'Source': 'https://github.com/djdarcy/unctools',  # Replace with your repo
    },
)
