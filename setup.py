#!/usr/bin/env python
import re

from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

with open('HISTORY.rst') as f:
    history = f.read()

# This hack is from http://stackoverflow.com/a/7071358/1231454;
# the version is kept in a seperate file and gets parsed - this
# way, setup.py doesn't have to import the package.
VERSIONFILE = 'btnamespace/_version.py'

with open(VERSIONFILE) as f:
    version_line = f.read()

version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)

setup(
    name='btnamespace',
    version=version,
    description='Isolate state on the Braintree sandbox during testing.',
    long_description=readme + '\n\n' + history,
    author='Simon Weber',
    author_email='simon@venmo.com',
    url='https://github.com/venmo/btnamespace',
    packages=['btnamespace'],
    package_dir={'btnamespace': 'btnamespace'},
    include_package_data=True,
    install_requires=[
        'bidict>=0.18.4,<0.19;python_version<="2.7"',
        'bidict>=0.18.4;python_version>"2.7"',
        'braintree>=3.46.0,<4;python_version<="2.7"',
        'braintree>=3.46.0;python_version>"2.7"',
        'future>=0.18.2',
        'mock',
    ],
    license='MIT',
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.6.*",
)
