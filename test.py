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

class Boilerplate(object):
    def attach(self, fn):
        setattr(self, fn.__name__, fn)
        return fn

    def setUp(self):
        @self.attach
        def identity(o):
            '''The identity function'''
            return o

        @self.attach
        def add1(n):
            '''+1-er'''
            return n + 1

        @self.attach
        def sum2(a, b):
            '''Return: a + b'''
            return a + b

        @self.attach
        def nothing(): '''I do nothing'''; 


    def tearDown(self):
        pass

##Test Cases##
class BeforeTests(Boilerplate, unittest.TestCase):
    def test_sanity(self):
        self.assertTrue(True, "True must be true")
        self.assertFalse(False, "False must be false")
        self.assertTrue(pydvice, "Must have pydvice to test")

    def test_before_simple(self):
        trace = {'ran': False}
        meta = {'doc': self.nothing.__doc__,
                'name': self.nothing.__name__}

        @pydvice.before(self.nothing)
        def store_trace():
            trace['ran'] = True

        self.assertEqual(self.nothing.__name__, meta['name'],
                         "Name of function mustn't change when advised.")
        self.assertTrue(self.nothing.__doc__.startswith(meta['doc']),
                        "The docstring must be the same for at least the beginning.")
        self.assertTrue(callable(self.nothing),
                        "The function needs to remain callable")

        self.nothing()

        self.assertTrue(trace['ran'],
                        "The advice should have ran")


if __name__ == '__main__':
    unittest.main()
