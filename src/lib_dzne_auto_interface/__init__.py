import argparse as _ap
import inspect as _ins


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


class _Knot(object):
    def _make_parser(self, *args, **kwargs):
        return _ap.ArgumentParser(
            *args,
            **kwargs,
            add_help=False,
        )
    def parser(self, *, add_help):
        return _ap.ArgumentParser(
            add_help=add_help,
            parents=[self._parser],
            description=self._parser.description,
        )
    def parse(self, args):
        return vars(self._parser.parse_args(args))
    @property
    def subknots(self):
    	return list(self._subknots)

class _Argument(_Knot):
    def __init__(self, *args, **kwargs):
        info = Information()
        info.kwargs = dict(*args, **kwargs)
        info.args = info.pop('option_strings', [])
        self._action_string = (info['action'] := info.get('action', 'store'))
        if self._action_string not in (
            'store', 
            #'store_const',
            'store_true', 
            'store_false', 
            #'append',
            #'append_const',
        ):
            raise ValueError()
        self._action = info.exec(self._parser.add_argument)
        self._parser = self._make_parser()
        self._subknots = list()
    @property
    def ispositional(self):
        return self.option_strings is None
    @property
    def option_strings(self):
        ans = self._action.option_strings
        if ans is None:
            return None
        else:
            return tuple(ans)
    @property
    def action(self):
        return self._action_string
    @property
    def dest(self):
        return self._action.dest
    @property
    def help(self):
    	return self._action.help
    @staticmethod
    def of_return(annotation, *, details={}):
        if callable(annotation):
            annotation = {'type': annotation}
        elif annotation is _ins.Parameter.empty:
            annotation = {}
        elif type(annotation) is str:
            annotation = {'help': annotation}
        return _Argument(**annotation, **details)

class _Parameter(_Knot):
    def __init__(self, value):
        self._subknots = self._get_subknots(value)
        parents = [x.parser(add_help=False) for x in self._subknots]
        self._parser = self._make_parser(parents=parents)
    @staticmethod
    def _get_subknots(parameter):
        if parameter.name.startswith('_'):
            raise ValueError(parameter.name)
        ann = parameter.annotation
        if parameter.kind is _ins.Parameter.VAR_KEYWORD:
            if ann is _ins.Parameter.empty:
                return []
            if type(ann) is list:
                return [_Argument(**x) for x in ann]
            if type(ann) is dict:
                return [_Argument(**v, dest=k) for k, v in ann.items()]
            raise ValueError()
        if ann is _ins.Parameter.empty:
            ann = dict()
        else:
            ann = dict(ann)
        ans = dict()
        ans['dest'] = parameter.name
        if parameter.kind is _ins.Parameter.POSITIONAL_ONLY:
            if parameter.default is not _ins.Parameter.empty:
                ans['nargs'] = '?'
                ans['default'] = parameter.default
        elif parameter.kind is _ins.Parameter.VAR_POSITIONAL:
            ans['nargs'] = '*'
        elif parameter.kind is _ins.Parameter.KEYWORD_ONLY:
            if 'option_strings' not in ann.keys():
                ann['option_strings'] = ['-' + parameter.name.replace('_', '-')]
            if parameter.default is _ins.Parameter.empty:
                ans['required'] = True
            else:
                ans['required'] = False
                ans['default'] = parameter.default
        else:
            raise ValueError()
        ans = _Argument(**ans, **ann)
        return [ans]


class _Main(_Knot):
	def run_cli(self, args):
		kwargs = self.parse(args)
		self._run(kwargs)
    def run_gui(self):
    	#implement!
    	#launch root window
    	raise NotImplementedError()
    def _run(self, kwargs):
        raise NotImplementedError()
    @property
    def description(self):
    	return self._parser.description


class _Callable(_Main):
    def __init__(self, value, return_details):
        self._value = value
        signature = _ins.signature(value)
        self._subknots = [_Parameter(p) for n, p in signature.parameters.items()]
        self._subknots += [
        	_Argument.of_return(
	            annotation=signature.return_annotation,
	            details=return_details,
	        )
	    ]
	    parents = [x.parser(add_help=False) for x in self.subknots]
        self._parser = self._make_parser(
            description=value.__doc__,
            parents=parents,
        )
    def _read_gui(self):
    	raise NotImplementedError()
    	#implement!
    def _run(self, kwargs):
        outfile = kwargs.pop(self.argument_of_return.dest)
        info = Information()
        for p in self.parameters:
        	for a in p.subknots:
        		value = kwargs.pop(a.dest)
        		if a.ispositional:
        			info.append(value)
        		else:
        			info[a.dest] = value
        if len(kwargs):
        	raise KeyError()
        result = info.exec(self._value)
        result = outfile.fileDataType(result)
        outfile.save(result)
    def _go(self):
    	kwargs = self._read_gui()
    	self._run(kwargs)
    @property
    def parameters(self):
    	return self.subknots[:-1]
    @property
    def argument_of_return(self):
    	return self.subknots[-1]

class _Uncallable(_Main):
    def __init__(self, value, return_details):
        self._dest = value._dest
        self._subknots = dict()
        parser = self._make_parser()
        subparsers = parser.add_subparsers(dest=value._dest)
        for n, m in _ins.getmembers(value):
            if n.startswith("_"):
                continue
            self._subknots[n] = make(m, return_details=return_details)
            subparsers.add_parser(
            	n.replace("_", "-"),
                parents=[self._subknots[n].parser(add_help=False)],
                add_help=True,
            )
        self._parser = self._make_parser(
            parents=[parser],
            description=value.__doc__,
        )
    def _run(self, kwargs):
        value = kwargs.pop(self.dest)
        return self.subknots[value]._run(kwargs)
    @property
    def dest(self):
    	return self._dest



def make(value, *, return_details):
    cls = _Callable if callable(value) else _Uncallable
    return cls(value, return_details=return_details)

        