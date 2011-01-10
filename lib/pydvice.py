import uuid
import copy
import types
import functools

def make_consuming_chain(*functions, **kwargs):
    '''
    Return a function that will call functions in sequence, passing the return down the chain of functions
    '''
    return reduce(lambda acc, f: lambda *args, **kwargs: f(acc(*args, **kwargs)), functions)


class before(object):
    '''Definition of before advice'''
    def __init__(self, fun, **options):
        options = dict({}, **options)
        self.fun = types.FunctionType(fun.func_code,
                                      fun.func_globals,
                                      fun.__name__,
                                      fun.func_defaults,
                                      fun.func_closure)

        shadow_name = 'advice_shadow_%s' % uuid.uuid4().hex

        caller = eval(compile('lambda *a, **k: %s.run(*a, **k)' % shadow_name,
                              '<pydvice.before>', 'eval'))

        fun.func_code = types.FunctionType(caller.func_code,
                                           fun.func_globals,
                                           fun.__name__,
                                           fun.func_defaults,
                                           fun.func_closure).func_code
        fun.func_globals.update(**{shadow_name: self})


    def run(self, *args, **kwargs):
        print "Should run before advice:", self.advice
        print "Then call:", self.fun
        self.advice(*args, **kwargs)
        return self.fun(*args, **kwargs)

    def __call__(self, advice):
        print "Registering advice %s => S(%s)" % (advice, self)
        self.advice = advice
        return self.run
