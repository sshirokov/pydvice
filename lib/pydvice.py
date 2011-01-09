
class before(object):
    '''Definition of before advice'''
    def __init__(self, fun, **options):
        options = dict({}, **options)
        self.fun = fun

    def run(self, *args, **kwargs):
        print "Should run before advice:", self.advice
        print "Then call:", self.fun
        return self.fun(*args, **kwargs)

    def __call__(self, advice):
        self.advice = advice

        self.run.__func__.__name__ = self.fun.__name__
        self.run.__func__.__doc__  = self.fun.__doc__
        return self.run
