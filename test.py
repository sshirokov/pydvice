#!/usr/bin/env python
import sys, os, types
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
        MAGIC = 'is everywhere'
        MORE_MAGIC = 'is impossible'

        @self.attach
        def closure():
            return MAGIC
        closure.MAGIC = MAGIC

        @self.attach
        def closure2():
            return MAGIC, MORE_MAGIC
        closure2.MAGIC = MAGIC
        closure2.MORE_MAGIC = MORE_MAGIC


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
        pydvice.reset()

##Test Cases##
class SanityChecks(Boilerplate, unittest.TestCase):
    def test_sanity(self):
        self.assertTrue(True, "True must be true")
        self.assertFalse(False, "False must be false")
        self.assertTrue(pydvice, "Must have pydvice to test")

    def test_cant_init_pydvice(self):
        from pydvice import PydviceError
        self.assertRaises(PydviceError, pydvice)

class PositionTests(Boilerplate, unittest.TestCase):
    def setUp(self):
        super(PositionTests, self).setUp()
        self.runs = []

        @self.attach
        @pydvice.before(self.identity)
        def a(*a, **k):
            self.runs.append('a')

        @self.attach
        @pydvice.before(self.identity)
        def b(*a, **k):
            self.runs.append('b')

        @self.attach
        @pydvice.before(self.identity)
        def c(*a, **k):
            self.runs.append('c')

        @self.attach
        @pydvice.before(self.identity)
        def d(*a, **k):
            self.runs.append('d')


    def test_advice_symbolic_positions(self):
        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad1')

        #Positional advice
        @pydvice.before(self.identity, position='first')
        def first(*a, **k):
            self.runs.append('first')

        @pydvice.before(self.identity, position='last')
        def last(*a, **k):
            self.runs.append('last')

        @pydvice.before(self.identity)
        def pad2(*a, **k):
            self.runs.append('pad2')


        self.assertTrue(self.identity(self) is self,
                         "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs[0], 'first',
                         "Advice with position='first' should run first, was: %s" % self.runs)
        self.assertEqual(self.runs[-1], 'last',
                         "Advice with position='first' should run first, was: %s" % self.runs)
        self.assertTrue(len(self.runs[1:-1]),
                        "More advice than just first and last should run, runs: %s" % self.runs)

    def test_advice_relative_positions(self):
        @pydvice.before(self.identity, position={'after': self.c})
        def after_c(*a, **k):
            self.runs.append('after_c')

        @pydvice.before(self.identity, position={'before': self.b})
        def before_b(*a, **k):
            self.runs.append('before_b')

        self.assertTrue(self.identity(self) is self,
                        "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs[self.runs.index('c') + 1], 'after_c',
                         "after_c advice is not running after c, runs: %s" % self.runs)
        self.assertEqual(self.runs[self.runs.index('b') - 1], 'before_b',
                         "before_b advice is not running before b, runs: %s" % self.runs)

    def test_advice_absolute_position_clamps(self):
        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad1')

        @pydvice.before(self.identity, position=999)
        def forever(*a, **k):
            self.runs.append('999')

        @pydvice.before(self.identity, position=-100)
        def minus_forever(*a, **k):
            self.runs.append('-100')

        @pydvice.before(self.identity)
        def pad2(*a, **k):
            self.runs.append('pad2')

        self.assertTrue(self.identity(self) is self,
                         "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs[0], '-100',
                         "Advice with position=N<0 should run first, was: %s" % self.runs)
        self.assertEqual(self.runs[-1], '999',
                         "Advice with position=N>max' should run last, was: %s" % self.runs)
        self.assertTrue(len(self.runs[1:-1]),
                        "More advice than just first and last should run, runs: %s" % self.runs)


    def test_advice_absolute_positions(self):
        @pydvice.before(self.identity, position=3)
        def third(*a, **k):
            self.runs.append('third')

        @pydvice.before(self.identity, position=2)
        def second(*a, **k):
            self.runs.append('second')

        @pydvice.before(self.identity, position=4)
        def fourth(*a, **k):
            self.runs.append('fourth')

        self.assertTrue(self.identity(self) is self,
                        "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs.index('third'), 3,
                         "third advice should be positioned at 3, runs: %s" % self.runs)
        self.assertEqual(self.runs.index('second'), 2,
                         "second advice should be positioned at 2, runs: %s" % self.runs)
        self.assertEqual(self.runs.index('fourth'), 4,
                         "fourth advice should be positioned at 4, runs: %s" % self.runs)

    def test_equal_absolute_positions_sort_by_creation(self):
        @pydvice.before(self.identity, position=0)
        def firstA(*a, **k):
            self.runs.append('firstA')

        @pydvice.before(self.identity, position=0)
        def firstB(*a, **k):
            self.runs.append('firstB')

        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad1')

        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad2')

        self.assertTrue(self.identity(self) is self,
                        "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs[0:2], ['firstB', 'firstA'],
                         "The first two advices should be the two declared first, last declared 0, was: %s" % self.runs)

    def test_equal_symbolic_positions_sort_by_creation(self):
        @pydvice.before(self.identity, position='first')
        def firstA(*a, **k):
            self.runs.append('firstA')

        @pydvice.before(self.identity, position='first')
        def firstB(*a, **k):
            self.runs.append('firstB')

        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad1')

        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad2')

        self.assertTrue(self.identity(self) is self,
                        "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs[0:2], ['firstB', 'firstA'],
                         "The first two advices should be the two declared first, last declared first, was: %s" % self.runs)

    def test_equal_relative_positions_sort_by_creation(self):
        @pydvice.before(self.identity, position={'before': self.c})
        def before1(*a, **k):
            self.runs.append('before1')

        @pydvice.before(self.identity, position={'before': self.c})
        def before2(*a, **k):
            self.runs.append('before2')

        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad1')

        @pydvice.before(self.identity)
        def pad1(*a, **k):
            self.runs.append('pad2')

        self.assertTrue(self.identity(self) is self,
                        "Even despite the overwhelming amount of advice, identity should function")
        self.assertEqual(self.runs[self.runs.index('c') - 2:self.runs.index('c')], ['before1', 'before2'],
                         "The two advices before c should be the two declared {before: c}, last declared closer to c, was: %s" % self.runs)

class UsecaseTests(Boilerplate, unittest.TestCase):
    def setUp(self):
        import copy
        super(self.__class__, self).setUp()
        class TestClass(object):
            def meth(self, a):
                return a + 1

            @classmethod
            def classmeth(cls, b):
                return b + 2

            @staticmethod
            def staticmeth(c):
                return c + 3
        self.TestClass = copy.deepcopy(TestClass)

    def test_advice_runs_in_correct_order(self):
        runs = []

        @pydvice.after(self.identity)
        def after(r, args, kwargs):
            runs.append('after')
        @pydvice.before(self.identity)
        def before(o):
            runs.append('before')
        @pydvice.around(self.identity)
        def around(doit, *rest, **k):
            runs.append('around')
            doit()

        self.assertTrue(self is self.identity(self),
                        "identity should keep functioning even with many advice layers")
        self.assertEqual(runs, ['before', 'around', 'after'],
                         "The advice should be applied in the order: before->around->after got %s" % ('->'.join(runs)))

    def test_can_advise_instance_methods(self):
        trace = {'ran': False}

        @pydvice.before(self.TestClass.meth)
        def meth_advice(*args, **kwargs):
            trace['ran'] = True

        self.assertEqual(self.TestClass().meth(1), 2,
                         "The method should still function when advised.")
        self.assertTrue(trace['ran'],
                        "The advice should have ran when attached to a method.")

    def test_can_advise_classmethods(self):
        trace = {'ran': False}

        @pydvice.before(self.TestClass.classmeth)
        def meth_advice(*args, **kwargs):
            trace['ran'] = True

        self.assertEqual(self.TestClass().classmeth(1), 3,
                         "The classmethod should still function when advised.")
        self.assertTrue(trace['ran'],
                        "The advice should have ran when attached to a classmethod.")

    def test_can_advise_staticmethods(self):
        trace = {'ran': False}

        @pydvice.before(self.TestClass.staticmeth)
        def meth_advice(*args, **kwargs):
            trace['ran'] = True

        self.assertEqual(self.TestClass().staticmeth(1), 4,
                         "The staticmethod should still function when advised.")
        self.assertTrue(trace['ran'],
                        "The advice should have ran when attached to a staticmethod.")


class AroundTests(Boilerplate, unittest.TestCase):
    def test_have_after(self):
        self.assertTrue(pydvice.around,
                        "pydvice.around should probably exist.")

    def test_around_can_modify_arguments(self):
        @pydvice.around(self.identity)
        def replace_with_string(doit, result, **ak):
            doit(args=("HELLO",))

        self.assertEqual(self.identity(self), "HELLO",
                         "Around advice should be able to modify the parameters")

    def test_even_with_multiple_around_inner_should_run_once(self):
        trace = {'first': False, 'second': False}
        runs = []
        def testfun():
            runs.append("Running")
            return True

        @pydvice.around(testfun)
        def first(doit, *rest, **kwargs):
            trace['first'] = True
            doit()

        @pydvice.around(testfun)
        def second(doit, *rest, **kwargs):
            trace['second'] = True
            doit()

        self.assertTrue(testfun(),
                        "testfun should return True and no advices modify that")
        self.assertTrue(trace['first'] and trace['second'],
                        "Both advices did not run")
        self.assertEqual(len(runs), 1,
                         "The inner function should only run once unless asked to otherwise")

    def test_can_call_original(self):
        trace = {'ran': False, 'result': None}

        @pydvice.around(self.identity)
        def passive(doit, result, args, kwargs):
            doit()
            trace.update(ran=True,
                         result=result())

        self.assertTrue(self is self.identity(self),
                        "The advice given calls the original, so identity should keep working")
        self.assertTrue(trace['ran'],
                        "The advice should have noted its pass in the trace.")
        self.assertTrue(self is trace['result'],
                        "The advice should have access to the result, and it should be correct")

    def test_can_modify_return_with_helper(self):
        @pydvice.around(self.identity)
        def wrongify_identity(doit, result, args, kwargs):
            doit()
            result(self.identity)

        self.assertFalse(self is self.identity(self),
                         "The advice should have affected the return value")
        self.assertTrue(self.identity is self.identity(self),
                        "The result of self.identity() should now always be self.identity")

    def test_can_modify_return_with_return(self):
        @pydvice.around(self.identity)
        def wrongify_identity(doit, result, args, kwargs):
            doit()
            return self.identity

        self.assertFalse(self is self.identity(self),
                         "The advice should have affected the return value by returning itself")
        self.assertTrue(self.identity is self.identity(self),
                        "The result of self.identity() should now always be self.identity")

    def test_can_skip_calling_function(self):
        self.assertEqual(self.sum2(1, 1), 2,
                         "The advice should make this addition inconsistant, but always wrong")

        @pydvice.around(self.sum2)
        def suck_at_math(doit, result, args, kwargs):
            import random
            return sum(args) + random.randint(1, 10)

        self.assertNotEqual(self.sum2(1, 1), 2,
                            "The advice should make this addition inconsistant, but always wrong")

    def test_can_skip_dangerous_function(self):
        class TestException(Exception): pass
        def failure():
            raise TestException("This function should be suppressed by advice")
        self.assertRaises(TestException, failure)

        @pydvice.around(failure)
        def ignore(*a, **k):
            return "passed"

        try: self.assertEqual(failure(), "passed", "Failure should now be returning 'passed' and doing nothing")
        except TestException: self.fail("failure() proper should no longer run, and therefore not raise TestException")

class AfterTests(Boilerplate, unittest.TestCase):
    def test_multiple_after_apply_in_logical_order(self):
        output = []

        def a():
            output.append("a")

        @pydvice.before(a)
        def b():
            output.append("b")

        @pydvice.after(a)
        def c(r, **k):
            output.append("c")

        @pydvice.after(a)
        def d(r, **k):
            output.append("d")

        a()

        self.assertEqual(output, ['b', 'a', 'c', 'd'],
                         "The advice did not run in a logical order")

    def test_have_after(self):
        self.assertTrue(pydvice.after,
                        "pydvice.after should probably exist.")

    def test_no_return(self):
        trace = {'return': None, 'args': None, 'kwargs': None}

        @pydvice.after(self.identity)
        def set_trace(ret, args, kwargs):
            trace.update(**{'return': ret,
                            'args': args,
                            'kwargs': kwargs})

        self.assertTrue(self is self.identity(self),
                        "Identity should continue functioning with this advice")
        self.assertTrue(self is trace['return'],
                        "The trace should recieve the return value of the function")

    def test_new_return(self):
        trace = {'return': None, 'args': None, 'kwargs': None}

        @pydvice.after(self.identity)
        def set_trace(ret, args, kwargs):
            trace.update(**{'return': ret,
                            'args': args,
                            'kwargs': kwargs})
            return self.identity

        self.assertTrue(self.identity is self.identity(self),
                        "Identity should be returning in line with the new advice")
        self.assertTrue(self is trace['return'],
                        "The trace should recieve the return value of the original function")


class BeforeTests(Boilerplate, unittest.TestCase):
    def test_before_modify_params(self):
        @pydvice.before(self.identity)
        def make_it_cake_instead(o):
            return "I want cake %s" % (o)

        self.assertTrue(isinstance(self.identity(self), types.StringTypes),
                        "Identity should sudently find itself retruning strings.")
        self.assertTrue(self.identity(self).startswith("I want cake"),
                        "Identity should begin to exclaim it's hungry")

    def test_before_modify_multiple_params(self):
        @pydvice.before(self.sum2)
        def double_args(*args, **kwargs):
            return [i*2 for i in args], kwargs

        self.assertEqual(self.sum2(1, 1), 4,
                         "Arguments were not doubled")

    def test_advise_activation(self):
        trace = {'ran': False}

        @pydvice.before(self.identity, activate=False)
        def store_trace(o):
            trace['ran'] = True

        self.assertFalse(store_trace.advice.active,
                         "The store_trace advice should be disabled")
        self.assertTrue(self.identity(self) is self,
                        "Identity should continue to function")
        self.assertFalse(trace['ran'],
                         "The advice should not have run since it's disabled.")

        store_trace.advice.activate()

        self.assertTrue(store_trace.advice.active,
                         "The store_trace advice should be enabled now")
        self.assertTrue(self.identity(self) is self,
                        "Identity should continue to function")
        self.assertTrue(trace['ran'],
                         "The advice should have run since it's now enabled.")

    def test_advise_multivar_closure(self):
        trace = {'ran': False}

        @pydvice.before(self.closure2)
        def prove_it_again():
            trace['ran'] = True

        this, that = self.closure2()
        self.assertEqual((this, that), (self.closure2.MAGIC, self.closure2.MORE_MAGIC),
                         "Closure is malfunctioning.")
        self.assertTrue(trace['ran'], "The advice did not run")

    def test_advise_closure(self):
        trace = {'ran': False}

        @pydvice.before(self.closure)
        def prove_it():
            trace['ran'] = True

        this = self.closure()
        self.assertEqual(this, self.closure.MAGIC, "Closure is malfunctioning.")
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

        self.assertTrue(store_trace.advice,
                        "The advice function should have a reference to the advice object")
        self.assertTrue(isinstance(store_trace.advice, pydvice.before),
                        "The advice object should be an instance of the type of advice that created it")


if __name__ == '__main__':
    unittest.main()
