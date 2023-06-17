import tkinter as _tk
import tkinter.ttk as _ttk


class Stack(_tk.Frame):
    @property
    def levels(self):
        return tuple(self._levels)
    def __init__(self, master, *, factories):
        super().__init__(master)
        factories = list(factories)
        self._levels = list()
        for i, factory in enumerate(factories):
            self._levels.append(factory(self))
            padN = 10 if (i != 0) else 0
            padS = 10 if (i != (len(factories) - 1)) else 0
            self._levels[-1].pack(
                side='top',
                fill='x',
                padx=(0, 0),
                pady=(padN, padS),
            )
