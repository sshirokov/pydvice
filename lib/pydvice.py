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
        self.fun = copy.copy(fun)

        lambda self, meth, *a, **k: functools.partial(meth, self)(*a, **k)

        #This is doomed to fail.
        call = make_consuming_chain(lambda self: functools.partial(self.__class__.run, self),
                                    lambda part: {'loader': (lambda *a, **k: a[0](*a[1:], **k)),
                                                  'partial': part,
                                                  'wrap': lambda self: lambda *a, **k: self.loader(*([self.partial.func] + a),
                                                                                                    **k)},
                                    lambda info: lambda *a, **k: info['wrap'](info)

                                    #((lambda l, p, *a, **k: l(*([p.func] + a), **k)))
        )(self)

        fun.func_code = types.FunctionType(call.func_code,
                                           fun.func_globals,
                                           fun.__name__,
                                           fun.func_defaults,
                                           call.func_closure or ()).func_code


    def run(self, *args, **kwargs):
        print "Should run before advice:", self.advice
        print "Then call:", self.fun
        return self.fun(*args, **kwargs)

    def __call__(self, advice):
        print "Registering advice %s => S(%s)" % (advice, self)
        self.advice = advice
        return self.run
