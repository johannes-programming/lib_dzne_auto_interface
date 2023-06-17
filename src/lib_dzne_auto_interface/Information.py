
class Information(object):
    def __init__(self, *, args=[], kwargs={}):
        self.args = args
        self.kwargs = kwargs
    @property
    def args(self):
        return list(self._args)
    @args.setter
    def args(self, value):
        self._args = list(value)
    @property
    def kwargs(self):
        return dict(self._kwargs)
    @kwargs.setter
    def kwargs(self, value):
        self._kwargs = dict(value)
        if not all(type(k) is str for k, v in self._kwargs.items()):
            raise TypeError()
    def __add__(self, other):
        return Information(
            args = self.args + other.args,
            kwargs = dict(**self.kwargs, **other.kwargs),
        )
    def __getitem__(self, key):
        if type(key) in (int, slice):
            return self._args[key]
        if type(key) is str:
            return self._kwargs[key]
        raise TypeError()
    def __setitem__(self, key, value):
        if type(key) in (int, slice):
            a = list(self.args)
            a[key] = value
            self.args = a
            return
        if type(key) is str:
            self._kwargs[key] = value
            return
        raise TypeError()
    def __delitem__(self, key):
        if type(key) in (int, slice):
            a = list(self.args)
            del a[key]
            self.args = a
            return
        if type(key) is str:
            del self._kwargs[key]
            return
        raise TypeError()
    def __str__(self):
        ans = {"args":self.args, "kwargs":self.kwargs}
        ans = str(ans)
        return ans
    def __repr__(self):
        return str(self)
    def pop(self, key=-1, /, *args):
        if type(key) in (int, slice):
            return self._args.pop(key, *args)
        if type(key) is str:
            return self._kwargs.pop(key, *args)
        raise TypeError()
    def get(self, key, default=None, /):
        if type(key) in (int, slice):
            try:
                return self._args[key]
            except IndexError:
                return default
        if type(key) is str:
            return self._kwargs.get(key, default)
        raise TypeError()
    def append(self, value):
        self._args.append(value)
    def exec(self, func):
        return func(*self._args, **self._kwargs)


 
