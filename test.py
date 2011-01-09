#!/usr/bin/env python
import sys, os
import unittest

#Try 'just' importing pydvice,
# failing try looking in ./lib
# next to this file
try:
    import pydvice
except ImportError:
    sys.path.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'lib'
    ))
    import pydvice
