import uuid
import types
import functools

class with_attrs(object):
    '''
    Decorator to set function attributes
    '''
    def __init__(self, **kwargs):
        self.options = kwargs;

    def __call__(self, f):
        [setattr(f, opt, val) for (opt, val) in self.options.items()]
        return f

class pydvice(object):
    advised = {}

    @classmethod
    def defines(cls, name, advice=None):
        if not advice: return functools.partial(cls.defines, name)

        setattr(cls, name, advice)
        setattr(advice, 'position', name)
        cls.advised[name] = {}
        return advice

    @classmethod
    def _register(cls, position, fun, advice):
        cls.advised[position].setdefault(fun, []).append(advice)
        return cls.advised[position][fun]

    @classmethod
    def reset(cls):
        cls.deactivate_all()
        [[[a.unbind() for a in advices]
          for fun, advices in advised.items()]
         for advised in cls.advised.values()]
        cls.advised = dict([(name, {}) for name in cls.advised.keys()])

    @classmethod
    def deactivate_all(cls):
        [[[a.deactivate() for a in advices]
          for fun, advices in advised.items()]
         for advised in cls.advised.values()]


class BaseAdvice(object):
    active = None

    def __init__(self, fun, **options):
        self.options = dict({'activate': True},
                            **options)
        self.fun_ref = fun
        self.fun = types.FunctionType(fun.func_code,
                                      fun.func_globals,
                                      fun.__name__,
                                      fun.func_defaults,
                                      fun.func_closure)

        self.shadow_name = '__advice_shadow_%s' % uuid.uuid4().hex
        self.bind()
        if self.options['activate']: self.activate()

    def __call__(self, advice):
        pydvice._register(self.position, self.fun_ref, self)
        advice.advice = self

        self.advice = advice
        return advice


    @property
    def position(self): raise NotImplementedError
    def act(self, *a, **k): raise NotImplementedError

    def run(self, *a, **k):
        if self.active: return self.act(*a, **k)
        else: return self.fun(*a, **k)

    def bind(self):
        self.call_expr = dict(expr='lambda *a, **k: {magic} and {shadow}.run(*a, **k)',
                              shadow=self.shadow_name,
                              bound=False,
                              magic='0xface',
                              freevars=[])
        while not self.call_expr['bound']:
            caller = eval(compile(self.call_expr['expr'].format(**self.call_expr),
                                  '<pydvice.%s>' % self.position, 'eval'))
            try: self.fun_ref.func_code = types.FunctionType(caller.func_code,
                                                             self.fun_ref.func_globals,
                                                             self.fun_ref.__name__,
                                                             self.fun_ref.func_defaults,
                                                             self.fun_ref.func_closure).func_code
            except ValueError, e:
                if 'closure of length' not in str(e): raise

                self.call_expr['freevars'].append('__%s' % uuid.uuid4().hex)
                self.call_expr.update(
                    expr=reduce(lambda acc, var: \
                                    '(lambda {var}: {expr})(True)'.format(**dict(self.call_expr, var=var, expr=acc)),
                                self.call_expr['freevars'],
                                self.call_expr['expr']),
                    magic='(%s,)' % ','.join(self.call_expr['freevars'])
                )
            else:
                self.call_expr['bound'] = True
        self.fun_ref.func_globals.update(**{self.shadow_name: self})
        return self

    def unbind(self):
        self.fun_ref.func_code = self.fun.func_code
        self.fun_ref.func_globals.pop(self.shadow_name, None)
        return self

    def deactivate(self):
        self.active = False
        return self

    def activate(self):
        self.active = True
        return self


@pydvice.defines('before')
class Before(BaseAdvice):
    '''Definition of before advice'''
    def act(self, *args, **kwargs):
        self.advice(*args, **kwargs)
        return self.fun(*args, **kwargs)

@pydvice.defines('after')
class After(BaseAdvice):
    '''Definition of after advice'''
    def act(self, *args, **kwargs):
        r = self.fun(*args, **kwargs)
        ar = self.advice(r, args=args, kwargs=kwargs)
        return r if ar is None else ar

@pydvice.defines('around')
class Around(BaseAdvice):
    '''Definition of around advice'''
    def act(self, *args, **kwargs):
        @with_attrs(value=None)
        def result(new_result=None):
            if new_result: result.value = new_result
            return result.value
        def doit(): result(self.fun(*args, **kwargs))

        ar = self.advice(doit, result, args=args, kwargs=kwargs)

        return result() if ar is None else ar

