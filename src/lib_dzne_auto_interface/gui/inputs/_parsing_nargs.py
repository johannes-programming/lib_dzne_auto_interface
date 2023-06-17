import string as _str


def parse(text):
    return _Parse()(text)

class _Parse:

    @property
    def quoting(self):
        return bool(self.text[:self.index].count('"') % 2)

    @staticmethod
    def state(character):
        if type(character) is not str:
            raise TypeError
        if len(character) != 1:
            raise ValueError
        if character == '"':
            return 'quote'
        if character in _str.whitespace:
            return 'space'
        return 'letter'

    @property
    def current_character(self):
        return self.text[self.index]
    @property
    def previous_character(self):
        if self.index == 0:
            return ' '
        return self.text[self.index - 1]

    @property
    def current_state(self):
        return self.state(self.current_character)
    @property
    def previous_state(self):
        return self.state(self.previous_character)

    def __call__(self, text):
        if text.count('"') % 2:
            raise ValueError()
        self.text = text
        self.args = list()
        for self.index in range(len(self.text)):
            if self.run():
                self.args[-1] += self.current_character
        return self.args


    def run(self):
        if self.current_state == 'quote':
            return self.run_quote()
        if self.current_state == 'space':
            return self.run_space()
        if self.current_state == 'letter':
            return self.run_letter()
        raise NotImplementedError

    def run_space(self):
        return self.quoting

    def run_letter(self):
        if self.quoting:
            return True
        if self.previous_state == 'space':
            self.args.append("")
            return True
        if self.previous_state == 'letter':
            return True
        if self.previous_state == 'quote':
            raise ValueError
        raise NotImplementedError

    def run_quote(self):
        if self.quoting:
            return False
        if self.previous_state == 'space':
            self.args.append("")
            return False
        if self.previous_state == 'letter':
            raise ValueError
        if self.previous_state == 'quote':
            return True
        raise NotImplementedError
 
