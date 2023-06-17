import tkinter as _tk
import tkinter.messagebox as _msgbox
import tkinter.ttk as _ttk


class HelpButton(_ttk.Button):
    @classmethod
    def make(cls, master, *, message, title):
        if message is None:
            return None
        return cls(master, message=message, title=title)
    @property
    def title(self):
        return self._title
    @title.setter
    def title(self, value):
        self._title = str(value)
    @property
    def message(self):
        return self._message
    @message.setter
    def message(self, value):
        self._message = str(value)
    def __init__(self, master, *, title, message):
        super().__init__(master, command=self.show_help, text="help")
        self.title = title
        self.message = message
    def show_help(self):
        _msgbox.showinfo(
            title=self.title,
            message=self.message,
        )