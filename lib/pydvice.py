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

        call_expr = dict(expr='lambda *a, **k: {magic} and {shadow}.run(*a, **k)',
                         shadow=self.shadow_name,
                         bound=False,
                         magic='0xface',
                         freevars=[])
        while not call_expr['bound']:
            caller = eval(compile(call_expr['expr'].format(**call_expr),
                                  '<pydvice.before>', 'eval'))
            try: fun.func_code = types.FunctionType(caller.func_code,
                                                    fun.func_globals,
                                                    fun.__name__,
                                                    fun.func_defaults,
                                                    fun.func_closure).func_code
            except ValueError, e:
                if 'closure of length' not in str(e): raise

                call_expr['freevars'].append('__%s' % uuid.uuid4().hex)
                call_expr.update(
                    expr=reduce(lambda acc, var: \
                                    '(lambda {var}: {expr})(True)'.format(**dict(call_expr, var=var, expr=acc)),
                                call_expr['freevars'],
                                call_expr['expr']),
                    magic='(%s,)' % ','.join(call_expr['freevars'])
                )
            else:
                call_expr['bound'] = True
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
