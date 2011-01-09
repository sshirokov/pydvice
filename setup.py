#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name        = 'pydvice',
    version     = '0.0.0',
    description = "An attempted port of elisp's (defadvice ..) for python",
    author      = 'slava@hackinggibsons.com',
    url         = 'about:blank',

    package_dir = {'': "lib"},
    packages    = find_packages("lib"),

    py_modules  = ['pydvice']
)
