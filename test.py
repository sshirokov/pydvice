#!/usr/bin/env python
import sys, os
import unittest

#Try 'just' importing pydvice,
# failing try looking in ./lib
# next to this file
try:
    from pydvice import pydvice
except ImportError:
    sys.path.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'lib'
    ))
    from pydvice import pydvice

class Boilerplate(object):
    def attach(self, fn):
        setattr(self, fn.__name__, fn)
        return fn

    def setUp(self):
        @self.attach
        def closure():
            return self

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
        pydvice.deactivate_all()

##Test Cases##
class BeforeTests(Boilerplate, unittest.TestCase):
    def test_sanity(self):
        self.assertTrue(True, "True must be true")
        self.assertFalse(False, "False must be false")
        self.assertTrue(pydvice, "Must have pydvice to test")

    def test_advise_closure(self):
        trace = {'ran': False}

        @pydvice.before(self.closure)
        def prove_it():
            trace['ran'] = True

        this = self.closure()
        self.assertTrue(this is self, "Closure is malfunctioning.")
        self.assertTrue(trace['ran'], "The advice did not run")

    def test_multiple_advice(self):
        trace = {'first': False,
                 'second': False}

        @pydvice.before(self.nothing)
        def store_first():
            trace['first'] = True

        @pydvice.before(self.nothing)
        def store_first():
            trace['second'] = True

        self.assertFalse(trace['first'] or trace['second'], "Both before advices did not run")
        self.nothing()
        self.assertTrue(trace['first'] and trace['second'], "Both before advices did not run")

    def test_advise_lambda(self):
        argses = []
        fun = lambda x, y: x+y

        pydvice.before(fun)(
            lambda *a, **k: argses.append((a, k)))

        self.assertEqual(fun(1, 1), 2, "Lamda still functions")
        self.assertEqual(len(argses), 1, "Lamda advice did not run")
        self.assertEqual(argses[0], ((1, 1), {}), "The advice collected garbage")

    def test_return_remains(self):
        ob = {'secret': 'squirrel'}
        identities = []

        @pydvice.before(self.identity)
        def store_identity(o):
            identities.append(o)

        ob2 = self.identity(ob)
        self.assertTrue(ob is ob2, "Identity function fails after being advised")
        self.assertTrue(ob in identities, "The advice did not perform to spec")
        self.assertEqual(len(identities), 1, "The advice ran too many times")

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
