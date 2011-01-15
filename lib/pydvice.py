import uuid
import types
import functools

def make_consuming_chain(*functions, **kwargs):
    '''
    Return a function that will call functions in sequence, passing the return down the chain of functions
    '''
    return reduce(lambda acc, f: lambda *args, **kwargs: f(acc(*args, **kwargs)), functions)

def ranged(Min, Max, v):
    return {v < Min: Min,
            v > Max: Max}.get(True, v)

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
    _index = 0

    def __init__(self, *a, **k): raise PydviceError("pydvice class should not instantiated")

    @classmethod
    def next_index(cls):
        cls._index += 1
        return cls._index

    @classmethod
    def defines(cls, name, advice=None, **options):
        if not advice: return functools.partial(cls.defines, name, **options)

        advice._meta = options
        setattr(cls, name, advice)
        setattr(advice, 'position', name)

        return advice

    @classmethod
    def sort_fun_advice(cls, ad_list):
        def consider_position(it, ad):
            pos = ad.options['position']
            if not (isinstance(pos, types.DictType) or pos is None):
                print
                print [a.advice and a.advice.__name__ for a in it]
                print "Pre:", pos
                pos = ranged(0, len(it), {'first': 0,
                                          'last': len(it)}.get(pos, pos))
                print "Pos:", pos
                it.insert(pos, ad)
                print [a.advice and a.advice.__name__ for a in it]
            return it

        return make_consuming_chain(
            lambda al:          ([a for a in al if not a.options.has_key('position')],
                                 [a for a in al if a.options.has_key('position')]),
            lambda al_pal: (lambda al, pal:
                                (sorted(al, key = lambda a: a.key), pal))(*al_pal),
            lambda al_pal: (lambda al, pal:
                                reduce(consider_position, pal, al))(*al_pal),
            lambda al:          reversed(al),
            list)(ad_list)

    @classmethod
    def _register(cls, fun, advice):
        sorted_ads, ads = (lambda al: (cls.sort_fun_advice(al), al))(
            cls.advised.get(fun, []) + [advice.bind()]
        )

        if ads != sorted_ads:
            [a.unbind() for a in reversed(ads)]
            reduce(lambda fun, ad: ad.init_fun(fun) and ad.bind().fun_ref,
                   sorted_ads,
                   fun)

        cls.advised[fun] = sorted_ads
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
    options = {'activate': True}

    advice = None
    fun = None
    fun_ref = None
    shadow_name = None
    pydvice = pydvice
    index = None

    def __init__(self, fun, **options):
        self.index = self.pydvice.next_index()
        self.options = dict(self.options,
                            **options)
        self.shadow_name = '__advice_shadow_%s' % uuid.uuid4().hex

        self.init_fun(fun)
        self.pydvice._register(self.fun_ref, self)

        if self.options['activate']: self.activate()

    def sort_index(self, seq, **options):
        return seq

    @property
    def key(self):
        return (self._meta.get('priority', None),
                self.sort_index(self.index))


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
        call_expr = dict(expr='lambda *a, **k: {magic} and {shadow}.run(*a, **k)',
                         shadow=self.shadow_name,
                         bound=False,
                         magic='0xface',
                         freevars=[])
        while not call_expr['bound']:
            caller = eval(compile(call_expr['expr'].format(**call_expr),
                                  '<pydvice.%s>' % self.position, 'eval'))
            try: self.fun_ref.func_code = types.FunctionType(caller.func_code,
                                                             self.fun_ref.func_globals,
                                                             self.fun_ref.__name__,
                                                             self.fun_ref.func_defaults,
                                                             self.fun_ref.func_closure).func_code
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

    def __repr__(self):
        return '<%s(%s)[%s]->%s>' % (self.__class__.__name__,
                                     self.fun_ref.__name__,
                                     self.key,
                                     self.advice and self.advice.__name__)


@pydvice.defines('before', priority=33)
class Before(BaseAdvice):
    '''
    Definition of before advice

    Advice function must have compatible arguments with the advised function

    You may return an alternate set of arguments to use for the inner function:
      return (args,)
      return (args, kwargs)
    '''
    def act(self, *args, **kwargs):
        maybe_args = self.advice(*args, **kwargs)

        if maybe_args is not None:
            maybe_args = maybe_args if isinstance(maybe_args, types.TupleType) else (maybe_args,)

            try:
                args, kwargs = {1: (maybe_args, kwargs),
                                2: maybe_args}[len(maybe_args)]
            except KeyError: raise PydviceError("Invalid return from before filter")
        return self.fun(*args, **kwargs)

@pydvice.defines('after', priority=99)
class After(BaseAdvice):
    '''
    Definition of after advice

    Advice function called as follows:
      advice(return_of_call, args=args_to_function, kwargs=kwargs_to_function)

    Returning from the advice function alters the return of the advised function.
    '''
    def sort_index(self, seq):
        '''
        After advice application order must be inverted
        to maintain logical application order.

        TODO: Explain why
        '''
        return -super(After, self).sort_index(seq)

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

