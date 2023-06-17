
import argparse as _ap
import inspect as _ins
import tkinter as _tk
import tkinter.ttk as _ttk

import lib_dzne_auto_interface.gui.HelpButton as _HB
import lib_dzne_auto_interface.gui.inputs as _inputs
import lib_dzne_auto_interface.gui.Stack as _Stack
import lib_dzne_auto_interface.Information as _Info


class _KnotFrame(_tk.Frame):
    @property
    def knot(self):
        return self._knot
    def __init__(self, master, *, knot, **kwargs):
        super().__init__(master)
        self._knot = knot
        self._init(**kwargs)
    def parse(self):
        raise NotImplementedError


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

class _Argument(_Knot):
    class _Frame(_KnotFrame):
        def _init(self):
            self._labelFrame = self._add_labelFrame()
            self._helpButton = self._add_helpButton()
            self._argumentInput = self._add_argumentInput()
        def parse(self):
            args = self._argumentInput.get_args()
            kwargs = self.knot.parse(args)
            return kwargs
        def _add_labelFrame(self):
            ans = _tk.LabelFrame(
                self, 
                text=self.knot.dest,
            )
            ans.pack(fill='both', expand=True)
            return ans
        def _add_helpButton(self):
            if self.knot.help is None:
                return None
            ans = _HB.HelpButton(
                self._labelFrame,
                title=f"help: {self.knot.dest}",
                message=self.knot.help,
            )
            ans.pack(
                side='right',
                #fill='y',
                padx=10,
                pady=10,
            )
            return ans
        def _add_argumentInput(self):
            ans = _inputs.ArgumentInput(
                self._labelFrame, 
                argument=self.knot,
            )
            ans.pack(
                padx=10,
                pady=10,
                side='left',
                fill='both',
                expand=True,
            )
            return ans
    def __init__(self, *args, of_return=False, **kwargs):
        self._of_return = bool(of_return)
        self._subknots = list()
        info = _Info.Information()
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
    def action(self):
        return self._action_string
    @property
    def option_strings(self):
        return tuple(self._action.option_strings)
    @property
    def dest(self):
        return self._action.dest
    @property
    def nargs(self):
        return self._action.nargs
    @property
    def const(self):
        return self._action.const
    @property
    def default(self):
        return self._action.default
    @property
    def type(self):
        return self._action.type
    @property
    def choices(self):
        return self._action.choices
    @property
    def required(self):
        return self._action.required
    @property
    def help(self):
        return self._action.help
    @property
    def of_return(self):
        return self._of_return
    @classmethod
    def argument_of_return(cls, annotation, *, details={}):
        if annotation is _ins.Parameter.empty:
            return None
        ann = cls._details_from_annotation(annotation)
        return _Argument(**ann, of_return=True, **details)

class _Parameter(_Knot):
    class _Frame(_KnotFrame):
        def _init(self):
            self.stack = self._add_stack()
        def parse(self):
            ans = dict()
            for level in self.stack.levels:
                kwargs = level.parse()
                ans = dict(**ans, **kwargs)
            return ans
        def _add_stack(self):
            factories = [x.frame for x in self.knot.subknots]
            ans = _Stack.Stack(self, factories=factories)
            ans.pack(
                expand=True,
                fill='both',
            )
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
            return _Info.Information(kwargs=kwargs)
        dest, = self.dests
        if self.kind is _ins.Parameter.KEYWORD_ONLY:
            return _Info.Information(kwargs=kwargs)
        if self.kind is _ins.Parameter.VAR_POSITIONAL:
            return _Info.Information(args=kwargs[dest])
        if self.kind is _ins.Parameter.POSITIONAL_ONLY:
            return _Info.Information(args=[kwargs[dest]])
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
        dictionary = self.parse(args, add_help=True)
        self._run_dictionary(dictionary)
    def run_gui(self):
        root = _tk.Tk()
        frame = self.frame(root)
        frame.pack(fill='both', expand=True)
        root.mainloop()
    def run_dictionary(self, dictionary, /):
        dictionary = dict(dictionary)
        self._run_dictionary(dictionary)
    def _run_dictionary(self, dictionary):
        raise NotImplementedError()
    @property
    def description(self):
        return self._parser.description


class _Callable(_Main):
    class _Frame(_KnotFrame):
        def _init(self):
            self.buttonFrame = self._add_buttonFrame()
            self.helpButton = self._add_helpButton()
            self.goButton = self._add_goButton()
            self.stack = self._add_stack()
        def parse(self):
            ans = dict()
            for level in self.stack.levels:
                kwargs = level.parse()
                ans = dict(**ans, **kwargs)
            return ans
        def go(self):
            kwargs = self.parse()
            self.knot.run_dictionary(kwargs)
        def _add_buttonFrame(self):
            ans = _tk.Frame(self)
            ans.pack(
                side='bottom',
                fill='x',
                padx=0,
                pady=0,
            )
            return ans
        def _add_helpButton(self):
            ans = _HB.HelpButton.make(
                self.buttonFrame,
                title="help",
                message=self.knot.description,
            )
            if ans is None:
                return ans
            ans.pack(
                side='right',
                padx=10,
                pady=10,
            )
            return ans
        def _add_goButton(self):
            ans = _ttk.Button(
                self.buttonFrame,
                text="go",
                command=self.go,
            )
            ans.pack(
                side='right',
                padx=10,
                pady=10,
            )
            return ans
        def _add_stack(self):
            factories = [x.frame for x in self.knot.subknots]
            ans = _Stack.Stack(self, factories=factories)
            ans.pack(
                side='top',
                fill='x',
                padx=10,
                pady=10,
            )
            return ans
    def __init__(self, value, return_details):
        self._value = value
        signature = _ins.signature(value)
        self._parameters = [_Parameter(p) for n, p in signature.parameters.items()]
        self._argument_of_return = _Argument.argument_of_return(
            annotation=signature.return_annotation,
            details=return_details,
        )
        parents = [x.parser(add_help=False) for x in self.subknots]
        self._parser = self._make_parser(
            description=self.description,
            parents=parents,
        )
    def _run_dictionary(self, dictionary):
        if self.argument_of_return is None:
            outfile = None
        else:
            outfile = dictionary.pop(self.argument_of_return.dest)
        info = _Info.Information()
        for p in self.parameters:
            y = {x:dictionary.pop(x) for x in p.dests}
            info += p.information(y)
        if len(dictionary):
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
    class _Frame(_KnotFrame):
        def _init(self):
            self.buttonFrame = self._add_buttonFrame()
            self.helpButton = self._add_helpButton()
            self.notebook = self._add_notebook()#ttk.Notebook(container,**options)
            for name, subknot in self.knot.mains.items():
                subframe = subknot.frame(self.notebook)
                subframe.pack(
                    expand=True,
                    fill='both',
                )
                self.notebook.add(subframe, text=name)
        def _add_notebook(self):
            ans = _ttk.Notebook(self)
            ans.pack(
                side='top',
                fill='both',
                expand=True,
                padx=10,
                pady=10,
            )
            return ans
        def _add_buttonFrame(self):
            ans = _tk.Frame(self)
            ans.pack(
                side='bottom',
                fill='x',
                padx=0,
                pady=0,
            )
            return ans
        def _add_helpButton(self):
            if self.knot.description is None:
                return None
            ans = _HB.HelpButton(
                self.buttonFrame,
                title="help",
                message=self.knot.description,
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
    def _run_dictionary(self, dictionary):
        key = dictionary.pop(self.dest)
        return self._mains[key].run_dictionary(dictionary)
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
