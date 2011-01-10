import uuid
import types

class Before(object):
    '''Definition of before advice'''
    def __init__(self, fun, **options):
        options = dict({}, **options)
        self.fun_ref = fun
        self.fun = types.FunctionType(fun.func_code,
                                      fun.func_globals,
                                      fun.__name__,
                                      fun.func_defaults,
                                      fun.func_closure)

        self.shadow_name = '__advice_shadow_%s' % uuid.uuid4().hex

        caller = eval(compile('lambda *a, **k: %s.run(*a, **k)' % self.shadow_name,
                              '<pydvice.before>', 'eval'))

        fun.func_code = types.FunctionType(caller.func_code,
                                           fun.func_globals,
                                           fun.__name__,
                                           fun.func_defaults,
                                           fun.func_closure).func_code
        fun.func_globals.update(**{self.shadow_name: self})

    def run(self, *args, **kwargs):
        self.advice(*args, **kwargs)
        return self.fun(*args, **kwargs)

    def __call__(self, advice):
        self.advice = advice
        pydvice.advised['before'].setdefault(self.fun_ref, []).append(self)
        return self.run

class pydvice(object):
    advised = {'before': {},
               'around': {},
               'after': {}}

    before = Before

    @classmethod
    def deactivate_all(cls):
        #TODO: Deactivate, don't just forget about
        [cls.advised.update({key: {}}) for key in cls.advised.keys()]
