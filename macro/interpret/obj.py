'''
Object for saving an interpreted macro.
'''

from macro.util           import NULL_POSITION, NULL_TOKEN_ID
       
# For debug prints of an InterpretedMacro
def get_test_repr(macro_data):
    ret = []
    def render_tok(t):
        if not t: return ''
        if t.render_space_after: return t.get_render_desc() + ' '
        return t.get_render_desc()
    def render_list(tok_list):
        if not tok_list: return None
        return ''.join(map(render_tok, tok_list)).strip()
    for cmd in macro_data:
        for if_do in cmd.interpret:
            ret.append(map(render_list, if_do))
    return ret


class InterpretedMacro:
    '''InterpretedMacro

    Lightweight object for holding the results of a macro interpretation.
    '''
    def __init__(self, macro=None):
        # Actual macro.
        self.macro = macro

        # decoded macro length
        self.macro_len = 0

        # Whether or not this macro is saveable
        # Defaults to True unless found otherwise.
        self.macro_good = True

        # Per-line data.
        self.macro_data = []

        # Whether or not this macro had characters cleaned
        # or chanaged.
        self.macro_changed = False

    # Dumb accessors
    def add_cmd(self, cmd):
        if cmd: self.macro_data.append(cmd)
    def last(self):
        if self.macro_data: return self.macro_data[-1]
    def last_macro_token(self):
        last = self.last()
        if last: return last.last()
    def get_test_repr(self):
        return get_test_repr(self.macro_data)

    def __iter__(self):
        ''' Iterator for processed macros. '''
        return iter(self.macro_data)
    def __len__(self):
        ''' Iterator for processed macros. '''
        return len(self.macro_data)

    def __str__(self):
        return str(get_test_repr(self.macro_data))
    def __repr__(self):
        return str(get_test_repr(self.macro_data))
    


class InterpretedMacroCommand:
    '''InterpretedMacroCommand

    Wrapper around data for an individual command in a macro.
    '''
    # Constants for dictionary members
    def __init__(self, cmd=None, index=-1):
        self.cmd                   = cmd
        self.cmd_list              = []
        self.index                 = index
        self.cmd_str               = ''
        self.interpret             = []
        self.error                 = False
    def last(self):
        if self.cmd_list: return self.cmd_list[-1]
