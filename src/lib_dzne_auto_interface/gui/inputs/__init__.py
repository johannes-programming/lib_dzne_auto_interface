import tkinter as _tk
import tkinter.filedialog as _filedialog
import tkinter.scrolledtext as _st
import tkinter.ttk as _ttk

import lib_dzne_filedata as _fd

import lib_dzne_auto_interface.gui.inputs._parsing_nargs as _parsing
import lib_dzne_auto_interface.gui.Stack as _Stack


def get(master, *, argument):
    """Create an input widget. """
    dim = int(argument.nargs is not None)
    func = [
        _get_dim_0,
        _get_dim_1,
    ][dim]
    return func(master, argument=argument)


def _get_dim_0(master, *, argument):
    if argument.action == 'store_true':
        return None # FlagInput(master)
    if argument.action == 'store_false':
        return None # FlagInput(master)
    if argument.choices is not None:
        return ChoicesInput(master, choices=argument.choices)
    if _fd.is_File(argument.type):
        return FileInput(master, ext=argument.type(None).ext, of_return=argument.of_return)
    return TextInput(master)

def _get_dim_1(master, *, argument):
    if type(argument.nargs) is int:
        return NargsIntInput(master, argument=argument)
    if argument.nargs == '?':
        return QuestionInput(master, argument=argument)
    if argument.nargs in ('*', '+'):
        return NargsPluralInput(master)
    raise NotImplementedError






class _Input(_tk.Frame):
    def __init__(self, master, *, active=True, **kwargs):
        super().__init__(master)
        self._init(**kwargs)
        self.active = active
    @property
    def active(self):
        return self._active
    @active.setter
    def active(self, value):
        value = bool(value)
        self._config_active(value)
        self._active = value
    def get_args(self):
        raise NotImplementedError
    # for all non-abstract subclasses the following functions must be defined:
    #     _init
    #     _config_active
    #     get_args


class FlagInput(_Input):
    def _init(self):
        pass
    def _config_active(self, value):
        pass
    def get_args(self):
        return []


class ChoicesInput(_Input):
    @property
    def string(self):
        return self._stringVar.get()
    def _init(self, choices):
        self._stringVar = _tk.StringVar()
        self._combobox = _ttk.Combobox(self, textvariable=self._stringVar)
        choices = tuple(str(x) for x in choices)
        self._combobox['values'] = choices
    def _config_active(self, value):
        state = 'readonly' if value else 'disabled'
        self._combobox.config(state=state)
    def get_args(self):
        return [self.string]


class FileInput(_Input):
    @property
    def ext(self):
        return self._ext
    @property
    def of_return(self):
        return self._of_return
    @property
    def string(self):
        return self._stringVar.get()
    def _init(self, *, of_return, ext):
        self._ext = ext
        self._of_return = bool(of_return)
        self._button = _ttk.Button(self, command=self.browse, text="browse")
        self._button.pack(
            side='right',
            padx=(10, 0),
            pady=(0, 0),
        )
        self._stringVar = _tk.StringVar()
        self._entry = _ttk.Entry(self, textvariable=self._stringVar)
        self._entry.pack(
            side='left',
            fill='x',
            expand=True,
        )
    def _config_active(self, value):
        state = 'normal' if value else 'disabled'
        self._entry.config(state=state)
        self._button.config(state=state)
    def get_args(self):
        return [self.string]
    def browse(self):
        if self._of_return:
            func = _filedialog.asksaveasfilename
        else:
            func = _filedialog.askopenfilename
        filetype = "*" + self._ext
        filetypes = [(filetype, filetype)]
        file = func(filetypes=filetypes)
        if file is None:
            return
        if file == "":
            return
        self._stringVar.set(file)


class TextInput(_Input):
    @property
    def string(self):
        return self._text.get("1.0", "end-1c")
    def _init(self):
        self._text = _tk.Text(self)
        self._text.pack(expand=True, fill='both')
    def _config_active(self, value):
        state = 'normal' if value else 'disabled'
        self._text.config(state=state)
    def get_args(self):
        return [self.string]


class CheckableInput(_Input):
    @property
    def checked(self):
        return bool(self._intVar.get())
    def _init(self, *, factory, required, default=True, option_strings=[]):
        default = int(bool(default))
        self._intVar = _tk.IntVar()
        self._intVar.set(default)
        self._checkbutton = self._add_checkbutton(required)
        self._subinput = self._add_subinput(factory)
        self._option_strings = list(option_strings)
    def _config_active(self, value):
        self._subinput.active = value
        if self._checkbutton is not None:
            state = 'normal' if value else 'disabled'
            self._checkbutton.config(state=state)
    def get_args(self):
        ans = list()
        if not self.checked:
            return ans
        if len(self._option_strings):
            ans.append(self._option_strings[0])
        if self._subinput is None:
            return ans
        ans += self._subinput.get_args()
        return ans
    def _check_change(self):
        if self._subinput is not None:
            self._subinput.active = self.checked
    def _add_checkbutton(self, required):
        if required:
            return None
        ans = _ttk.Checkbutton(
            self, 
            command=self._check_change, 
            variable=self._intVar,
        )
        ans.pack(
            side='right',
            padx=(10, 0),
            pady=(0, 0),
        )
        return ans
    def _add_subinput(self, factory):
        ans = factory(self)
        if ans is None:
            return None
        padE = 0 if (self._checkbutton is None) else 10
        ans.pack(
            padx=(0, padE),
            pady=(0, 0),
            side='left',
            fill='both',
            expand=True,
        )
        return ans


class QuestionInput(CheckableInput):
    def _init(self, argument):
        if argument.nargs != '?':
            raise ValueError
        self._factory_argument = argument.change(nargs=None)
        super()._init(
            factory=self._factory, 
            required=False,
            option_strings=argument.option_strings,
        )
    def _factory(self, master):
        return get(master, argument=self._factory_argument)


class NargsIntInput(_Input):
    def _init(self, argument):
        if type(argument.nargs) is not int:
            raise TypeError
        if argument.nargs < 0:
            raise ValueError
        self._argument = argument
        factories = [self._factory] * argument.nargs
        self._stack = _Stack.Stack(self, factories=factories)
    def _factory(self, master):
        return _get_dim_0(master, argument=self._argument)
    def get_args(self):
        ans = list()
        for level in self._stack.levels:
            ans += level.get_args()
        return ans
    def _config_active(self, value):
        for level in self._stack.levels:
            level.active = value


class NargsPluralInput(_Input):
    def _init(self):
        self._scrolledText = _st.ScrolledText(self)
        self._scrolledText.pack(expand=True, fill='both')
    def _config_active(self, value):
        state = 'normal' if value else 'disabled'
        self._scrolledText.config(state=state)
    def get_args(self):
        ans = self._scrolledText.get("1.0", "end-1c")
        ans = _parsing.parse(ans)
        return ans


class ArgumentInput(CheckableInput):
    def _init(self, argument):
        self._factory_argument = argument.change(required=False)
        super()._init(
            factory=self._factory, 
            required=argument.required,
            option_strings=argument.option_strings,
        )
    def _factory(self, master):
        return get(master, argument=self._argument)












