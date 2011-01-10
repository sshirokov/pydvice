import uuid
import types

class pydvice(object):
    advised = {}

    @classmethod
    def defines(cls, name):
        def do_define(ad_cls):
            setattr(cls, name, ad_cls)
            setattr(ad_cls, 'position', name)
            cls.advised[name] = {}
            return ad_cls
        return do_define

    @classmethod
    def _register(cls, position, fun, advice):
        cls.advised[position].setdefault(fun, []).append(advice)
        return cls.advised[position][fun]

    @classmethod
    def _flush(cls):
        cls.deactivate_all()
        advised = {}

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
        if self.options['activate']: self.activate()

    def __call__(self, advice):
        pydvice._register(self.position, self.fun_ref, self)
        advice.advice = self

        self.advice = advice
        return advice


    @property
    def position(self): raise NotImplementedError
    def run(self, *a, **k): raise NotImplementedError

    def deactivate(self):
        self.fun_ref.func_code = self.fun.func_code
        self.fun_ref.func_globals.pop(self.shadow_name, None)
        self.active = False

    def activate(self):
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
        self.activate = True


@pydvice.defines('before')
class Before(BaseAdvice):
    '''Definition of before advice'''
    def run(self, *args, **kwargs):
        self.advice(*args, **kwargs)
        return self.fun(*args, **kwargs)
