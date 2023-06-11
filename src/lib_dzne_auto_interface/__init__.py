import argparse as _ap
import inspect as _ins
import tkinter as _tk
import tkinter.messagebox as _msgbox
import tkinter.ttk as _ttk


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
    def parse(self, args, *, add_help=False):
        return vars(self.parser(add_help=add_help).parse_args(args))
    def frame(self, master):
        return type(self)._Frame(master=master, knot=self)
    @staticmethod
    def _details_from_annotation(annotation):
        if annotation is _ins.Parameter.empty:
            return {}
        if callable(annotation):
            return {'type': annotation}
        if type(annotation) is str:
            return {'help': annotation}  
        return dict(annotation)      
    @property
    def subknots(self):
        return list(self._subknots)


class Checkbutton(_ttk.Checkbutton):
    def __init__(self, *args, **kwargs):
        self.intVar = _tk.IntVar()
        super().__init__(*args, variable=self.intVar, onvalue=1, offvalue=0, **kwargs)
        self.active = False
    @property
    def checked(self):
        return bool(self.intVar.get())
class HelpButton(_ttk.Button):
    @classmethod
    def make(cls, *args, message, **kwargs):
        if message is None:
            return None
        return cls(*args, message=message, **kwargs)
    def __init__(self, *args, title, message, **kwargs):
        super().__init__(*args, command=self.show_help, **kwargs)
        self.title = title
        self.message = message
    def show_help(self):
        _msgbox.showinfo(
            title=self.title,
            message=self.message,
        )
class SingleInput(_tk.Entry):
    def __init__(self, *args, **kwargs):
        self.stringVar = _tk.StringVar()
        super().__init__(*args, textvariable=self.stringVar, **kwargs)
    def get_args(self):
        return [self.stringVar.get()]
    @property
    def active(self):
        return self._active
    @active.setter
    def active(self, value):
        value = bool(value)
        if value:
            self.config(state='normal')
        else:
            self.config(state="disabled")
        self._active = value
class MultiInput(_tk.Text):
    @property
    def active(self):
        return self._active
    @active.setter
    def active(self, value):
        value = bool(value)
        if value:
            self.config(state='normal')
        else:
            self.config(state="disabled")
        self._active = value
    def get_args(self):
        ans = self.get("1.0", "end-1c")
        ans = ans.split('\n')
        return ans



class _Argument(_Knot):
    class _Frame(LabelFrame):
        def __init__(self, master, knot):
            super().__init__(master, text=knot.dest)
            self.knot = knot
            self.helpButton = self._add_helpButton()
            self.checkbutton = self._add_checkbutton()
            self.inputWidget = self._add_inputWigdet()
        @property
        def option_string(self):
            values = self.knot.option_strings
            if len(values):
                return values[0]
            else:
                return None
        @property
        def active:
            if self.checkbutton is None:
                return None
            return self.checkbutton.active
        def get_args(self):
            ans = list()
            if self.active is False:
                return ans
            if self.option_string is not None:
                ans.append(self.option_string)
            if self.inputWidget is not None:
                ans += self.inputWidget.get_args()
            return ans
        def parse(self):
            args = self.get_args()
            kwargs = self.knot.parse(args)
            return kwargs
        def check_change(self):
            self.inputWidget.active = self.checkbutton.checked
        def _add_helpButton(self):
            if self.knot.help is None:
                return None
            ans = HelpButton(
                self,
                title=f"help :{self.knot.dest}",
                message=self.knot.help,
            )
            ans.pack(
                side='right',
                padx=10,
                pady=10,
            )
            return ans
        def _add_checkbutton(self):
            if self.knot.required:
                return None
            ans = Checkbutton(
                self, 
                command=self.check_change,
            )
            ans.pack(
                side='right',
                padx=10,
                pady=10,
            )
            return ans
        def _add_inputWigdet(self):
            if self.knot.action == 'store_true':
                return None
            if self.knot.action == 'store_false':
                return None
            if self.knot.nargs is None:
                Ans = SingleInput
            else:
                Ans = MultiInput
            ans = Ans(self)
            ans.pack(
                padx=10,
                pady=10,
            )
    def __init__(self, *args, **kwargs):
        self._subknots = list()
        info = Information()
        info.kwargs = dict(*args, **kwargs)
        info.args = info.pop('option_strings', [])

        # action
        info['action'] = info.get('action', 'store')
        self._action_string = info['action']
        if self._action_string not in (
            'store', 
            #'store_const',
            'store_true', 
            'store_false', 
            #'append',
            #'append_const',
        ):
            raise ValueError()

        self._parser = self._make_parser()
        self._action = info.exec(self._parser.add_argument)
    @property
    def positional(self):
        return not bool(len(self.option_strings))
    @property
    def option_strings(self):
        return tuple(self._action.option_strings)
    @property
    def action(self):
        return self._action_string
    @property
    def dest(self):
        return self._action.dest
    @property
    def nargs(self):
        return self._action.nargs
    @property
    def help(self):
        return self._action.help
    @property
    def required(self):
        return self._action.required
    @classmethod
    def of_return(cls, annotation, *, details={}):
        if annotation is _ins.Parameter.empty:
            return None
        ann = cls._details_from_annotation(annotation)
        return _Argument(**ann, **details)

class _Parameter(_Knot):
    class _Frame(_tk.Frame):
        def __init__(self, master, *, knot):
            super().__init__(master)
            self.knot = knot
            self.subframes = list()
            for item in enumerate(self.knot.subknots):
                self.subframes.append(self._subframe(*item, len(self.knot.subknots)))
        def _subframe(self, index, argument, length):
            ans = argument.frame(self)
            padN = 0 if (index == 0) else 10
            padS = 0 if (index == length - 1) else 10
            ans.pack(
                side='top',
                padx=(0, 0),
                pady=(padN, padS),
            )
        def parse(self):
            ans = dict()
            for subframe in self.subframes:
                kwargs = subframe.parse()
                ans = dict(**ans, **kwargs)
            return ans
    def __init__(self, value):
        self._subknots = self._get_subknots(value)
        parents = [x.parser(add_help=False) for x in self._subknots]
        self._parser = self._make_parser(parents=parents)
        self._kind = value.kind
        #self.information({x:None for x in self.dests})
    def information(self, kwargs, /):
        if set(kwargs.keys()) != set(self.dests):
            raise KeyError()
        if self.kind is _ins.Parameter.VAR_KEYWORD:
            return Information(kwargs=kwargs)
        dest, = self.dests
        if self.kind is _ins.Parameter.KEYWORD_ONLY:
            return Information(kwargs=kwargs)
        if self.kind is _ins.Parameter.VAR_POSITIONAL:
            return Information(args=kwargs[dest])
        if self.kind is _ins.Parameter.POSITIONAL_ONLY:
            return Information(args=[kwargs[dest]])
        raise ValueError()
    @property
    def dests(self):
        return [a.dest for a in self.subknots]
    @property
    def kind(self):
        return self._kind
    @classmethod
    def _get_subknots(cls, parameter):
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
        ann = cls._details_from_annotation(ann)
        ans = dict()
        ans['dest'] = parameter.name
        if parameter.kind is _ins.Parameter.POSITIONAL_ONLY:
            if parameter.default is not _ins.Parameter.empty:
                ans['nargs'] = '?'
                ans['default'] = parameter.default
        elif parameter.kind is _ins.Parameter.VAR_POSITIONAL:
            ans['nargs'] = '*'
            ans['default'] = tuple()
        elif parameter.kind is _ins.Parameter.KEYWORD_ONLY:
            if 'option_strings' not in ann.keys():
                ann['option_strings'] = ['-' + parameter.name.replace('_', '-')]
            if parameter.default is _ins.Parameter.empty:
                ans['required'] = True
            else:
                ans['required'] = False
                ans['default'] = parameter.default
        else:
            raise ValueError(f"The parameter {parameter} is not of a kind that can be included into auto-interface. ")
        ans = _Argument(**ans, **ann)
        return [ans]


class _Main(_Knot):
    def run_cli(self, args):
        kwargs = self.parse(args, add_help=True)
        self._run(kwargs)
    def run_gui(self):
        root = _tk.Tk()
        frame = self.frame(root)
        frame.pack(fill=_tk.BOTH, expand=True)
        root.mainloop()
    def _run(self, kwargs):
        raise NotImplementedError()
    @property
    def description(self):
        return self._parser.description


class _Callable(_Main):
    class _Frame(_tk.Frame):
        def __init__(self, master, *, knot):
            super().__init__(master)
            self.knot = knot
            self._init()
        def _init(self):
            self.buttonFrame = _tk.Frame(self)
            self.buttonFrame.pack(
                side='bottom',
                fill=_tk.X,
            )
            self.helpButton = HelpButton(
                self.buttonFrame,
                title="help",
                message=self.description,
            )
            self.helpButton.pack(
                side='right',
                padx=10,
                pady=10,
            )
            self.goButton = _ttk.Button(
                self.buttonFrame,
                command=self.go,
            )
            self.goButton.pack(
                side='right',
                padx=10,
                pady=10,
            )
            self.subframes = list()
            for subknot in self.knot.subknots:
                subframe = subknot.frame(master=self, knot=self.knot)
                subframe.pack(
                    side='top',
                    fill=_tk.X,
                    padx=10,
                    pady=10,
                )
                self.subframes.append(subframe)
        def parse(self):
            ans = dict()
            for subframe in self.subframes:
                kwargs = subframe.parse()
                ans = dict(**ans, **kwargs)
            return ans
        def go(self):
            kwargs = self.parse()
            self.knot._run(kwargs)
    def __init__(self, value, return_details):
        self._value = value
        signature = _ins.signature(value)
        self._parameters = [_Parameter(p) for n, p in signature.parameters.items()]
        self._argument_of_return = _Argument.of_return(
            annotation=signature.return_annotation,
            details=return_details,
        )
        parents = [x.parser(add_help=False) for x in self.subknots]
        self._parser = self._make_parser(
            description=self.description,
            parents=parents,
        )
    def _run(self, kwargs):
        if self.argument_of_return is None:
            outfile = None
        else:
            outfile = kwargs.pop(self.argument_of_return.dest)
        info = Information()
        for p in self.parameters:
            y = {x:kwargs.pop(x) for x in p.dests}
            info += p.information(y)
        if len(kwargs):
            raise KeyError()
        result = info.exec(self._value)
        if outfile is None:
            return
        result = outfile.fileDataType(result)
        outfile.save(result)
    @property
    def _subknots(self):
        ans = self.parameters
        if self.argument_of_return is not None:
            ans.append(self.argument_of_return)
        return ans
    @property
    def parameters(self):
        return list(self._parameters)
    @property
    def argument_of_return(self):
        return self._argument_of_return
    @property
    def description(self):
        return self._value.__doc__

class _Uncallable(_Main):
    class _Frame(_tk.Frame):
        def __init__(self, master, *, knot, **kwargs):
            super().__init__(master, **kwargs)
            self.knot = knot
            self._init()
        def _init(self):
            self.buttonFrame = self._add_buttomFrame()
            self.helpButton = self._add_helpButton()
            self.notebook = self._add_notebook()#ttk.Notebook(container,**options)
            for name, subknot in self.mains.items():
                subframe = subknot.frame(self)
                self.notebook.add(subframe, text=name)
        def _add_notebook(self):
            ans = _ttk.Notebook(self)
            ans.pack(
                side='top',
                file='both',
                padx=10,
                pady=10,
            )
            return ans
        def _add_buttomFrame(self):
            ans = _tk.Frame(self)
            ans.pack(
                side='bottom',
                fill='x',
                padx=0,
                pady=0,
            )
            return ans
        def _add_helpButton(self):
            if self.description is None:
                return None
            ans = HelpButton(
                self.buttonFrame,
                title="help",
                message=self.description,
            )
            ans.pack(
                side='right',
                padx=10,
                pady=10,
            )
    def __init__(self, value, return_details):
        self._dest = value._dest
        self._description = value.__doc__
        self._mains = dict()
        parser = self._make_parser()
        subparsers = parser.add_subparsers(dest=value._dest)
        for n, m in _ins.getmembers(value):
            if n.startswith("_"):
                continue
            name = n.replace('_', '-')
            self._mains[name] = make(m, return_details=return_details)
            parent = self._mains[name].parser(add_help=False)
            subparser = subparsers.add_parser(
                n.replace("_", "-"),
                parents=[parent],
                add_help=True,
            )
            subparser.description = parent.description
        self._parser = self._make_parser(
            parents=[parser],
            description=value.__doc__,
        )
    def _run(self, kwargs):
        value = kwargs.pop(self.dest)
        return self._mains[value]._run(kwargs)
    @property
    def description(self):
        return self._description
    @property
    def dest(self):
        return self._dest
    @property
    def mains(self):
        return dict(self._mains)
    @property
    def _subknots(self):
        return list(self._mains.values())



def make(value, *, return_details):
    cls = _Callable if callable(value) else _Uncallable
    return cls(value, return_details=return_details)

        