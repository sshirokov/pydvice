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

class PydviceError(Exception): pass

class pydvice(object):
    advised = {}

    def __init__(self, *a, **k): raise PydviceError("pydvice class should not instantiated")

    @classmethod
    @with_attrs(repo={})
    def original_fun(cls, fun):
        self = cls.original_fun
        if fun in self.repo.keys():
            fun = self.repo[fun]
        else:
            self.repo[fun] = types.FunctionType(fun.func_code,
                                                fun.func_globals,
                                                fun.__name__,
                                                fun.func_defaults,
                                                fun.func_closure)
            fun = self.repo[fun]
        return fun

    @classmethod
    def defines(cls, name, advice=None, **options):
        if not advice: return functools.partial(cls.defines, name, **options)

        advice._meta = options
        setattr(cls, name, advice)
        setattr(advice, 'position', name)
        setattr(advice, 'pydvice', cls)
        return advice

    @classmethod
    def _register(cls, fun, advice):
        sort_k = {'key': lambda a: a._meta.get('priority', None), 'reverse': True}
        sorted_ads, ads = (lambda al: (sorted(al, **sort_k), al))(
            cls.advised.get(fun, []) + [advice.bind()]
        )

        if ads != sorted_ads:
            [a.unbind() for a in reversed(ads)]
            reduce(lambda fun, ad: ad.init_fun(fun) and ad.bind().fun_ref,
                   sorted_ads,
                   fun)

        cls.advised[fun] = ads
        return advice

    @classmethod
    def reset(cls):
        cls.deactivate_all()
        [[a.unbind() for a in reversed(advice)]
         for fun, advice in cls.advised.items()]
        cls.advised = {}

    @classmethod
    def deactivate_all(cls):
        [advice.deactivate()
         for funlists in cls.advised.values()
         for advice in funlists]

class BaseAdvice(object):
    _meta = None
    active = None

    fun = None
    fun_ref = None

    def __init__(self, fun, **options):
        self.options = dict({'activate': True},
                            **options)
        self.shadow_name = '__advice_shadow_%s' % uuid.uuid4().hex

        self.pydvice.original_fun(self.init_fun(fun))
        self.pydvice._register(self.fun_ref, self)

        if self.options['activate']: self.activate()


    def init_fun(self, fun):
        fun = fun if isinstance(fun, types.FunctionType) else fun.im_func
        self.fun_ref = fun
        self.fun = types.FunctionType(fun.func_code,
                                      fun.func_globals,
                                      fun.__name__,
                                      fun.func_defaults,
                                      fun.func_closure)
        return fun


    def __call__(self, advice):
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


@pydvice.defines('before', priority=33)
class Before(BaseAdvice):
    '''
    Definition of before advice

    Advice function must have compatible arguments with the advised function
    '''
    def act(self, *args, **kwargs):
        self.advice(*args, **kwargs)
        return self.fun(*args, **kwargs)

@pydvice.defines('after', priority=99)
class After(BaseAdvice):
    '''
    Definition of after advice

    Advice function called as follows:
      advice(return_of_call, args=args_to_function, kwargs=kwargs_to_function)

    Returning from the advice function alters the return of the advised function.
    '''
    def act(self, *args, **kwargs):
        r = self.fun(*args, **kwargs)
        ar = self.advice(r, args=args, kwargs=kwargs)
        return r if ar is None else ar

@pydvice.defines('around', priority=66)
class Around(BaseAdvice):
    '''
    Definition of around advice

    Advice function called as follows:
      advice(doit, result, args=args_to_function, kwargs=kwargs_to_function)

    Special params
      doit: A callable of no arguments which results in a function call and stores the result.

      result: A callable of either 0 or 1 arguments. Without arguments returns the current
              return value. With argument sets the value to be returned.

    Either calling result() with a value or returning from the advice will alter the return
    of the advised function.
    '''
    def act(self, *args, **kwargs):
        @with_attrs(value=None)
        def result(new_result=None):
            if new_result is not None: result.value = new_result
            return result.value
        def doit(): result(self.fun(*args, **kwargs))

        return result(self.advice(doit, result, args=args, kwargs=kwargs))

