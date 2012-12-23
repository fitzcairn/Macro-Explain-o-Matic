'''
Macro token classes.
'''

import re
from macro.util                 import is_number, NULL_POSITION, NULL_TOKEN_ID, NULL_TOKEN

from macro.language.arg         import Arg, ARG_MAP
from macro.language.option      import Option, OPTION_MAP
from macro.language.parameter   import Parameter, PARAM_MAP
from macro.language.target      import TargetUnit, TARGET_MAP
from macro.language.verb        import Verb, VERB_MAP

from macro.lex.warnings         import WARN_TOGGLE, WARN_UNKNOWN_VERB
from macro.lex.ids              import *
from macro.lex.token_base       import MacroTokenBase

# Token factory API--create a macro token
def create_token(token_type=COMMAND_VERB, token_id=NULL_TOKEN_ID, data=None,
                 start=NULL_POSITION, end=NULL_POSITION, space_after=False,
                 interp_space_after=False, index=0):
    ''' Create a MacroToken instance and return it.'''
    new_token = MacroToken(token_type, token_id, data, start, end, space_after, interp_space_after, index)

    # If we don't have data, done.
    if new_token.data is None: return new_token

    # Set language attributes for some language primitives.
    if token_type == PARAMETER or token_type == TOGGLE:
        # Do we already know what this parameter is?  If so, done.
        if _lookup_token_attrs(new_token, PARAM_MAP):
            return new_token
        else:
            new_token.attrs = Parameter(token=new_token)

    elif token_type == OPTION_WORD:
        new_token.data = new_token.data.lower()
        if not _lookup_token_attrs(new_token, OPTION_MAP):
            new_token.attrs = Option(token=new_token)

    elif token_type == OPTION_ARG:
        if _lookup_token_attrs(new_token, ARG_MAP):
            return new_token
        if _lookup_token_attrs(new_token, ARG_MAP,
                               data=new_token.data.lower()):
            new_token.data = new_token.data.lower()
        elif _lookup_token_attrs(new_token, ARG_MAP,
                               data=new_token.data.upper()):
            new_token.data = new_token.data.upper()
        elif new_token.data_type is int:
            new_token.attrs = Arg(token=new_token,
                                  is_numeric=True)
        else:
            new_token.attrs = Arg(token=new_token)            

    elif token_type == TARGET_OBJ:
        # If this is part of a chain (i.e. Unit-target),
        # make sure we render the target WITHOUT any dash.
        lookup = new_token.data
        if new_token.data[-0] == '-': lookup = lookup[1:]
        if new_token.data[-1] == '-': lookup = lookup[:-1]
        # Get specific language attributes
        if _lookup_token_attrs(new_token, TARGET_MAP, data=lookup):
            return new_token
        # Is the lowercase version in the map?
        elif _lookup_token_attrs(new_token, TARGET_MAP,
                                data=lookup.lower()):
            new_token.data = new_token.data.lower()
        # Is this a %t?
        elif new_token.data == "%t" or new_token.data == "%T":
            new_token.attrs = TargetUnit(token=new_token,
                                         perc_target=True)
        # Named unit.
        else:
            new_token.render_desc = lookup
            new_token.attrs = TargetUnit(token=new_token)


    elif token_type == COMMAND_VERB or token_type == META_COMMAND_VERB:
        new_token.data = new_token.data.lower()
        # Is this an unknown verb?  If so, file a warning.
        if not _lookup_token_attrs(new_token, VERB_MAP):
            new_token.attrs = Verb(token=new_token)
            new_token.warn  = (WARN_UNKNOWN_VERB,)

    elif token_type == COMMENTED_LINE:
        _lookup_token_attrs(new_token, VERB_MAP, data="COMMENT")

    return new_token


# Helper to make lookups into attribute maps easier.
def _lookup_token_attrs(token, attr_map, data=None):
    if not data: data = token.data
    if data in attr_map:
        attrs = attr_map[data]
        attrs.token = token
        token.attrs = attrs
        return True
    return False


# MacroToken class, which represents a token.
class MacroToken(MacroTokenBase):
    """MacroToken

    Data structure returned by a MacroTokenizer instance.  Each
    MacroToken represents an actionable unit from a macro command, and
    contains a label, the data making up the token, the start index,
    and the end index (in the original string).

    The language description data structures contribute attributes to
    each token.  See language.py for detals.
    """
    space_norm_re = re.compile('(\s{2,})')

    def __init__(self, token_type, token_id=NULL_TOKEN_ID, data=None,
                 start=NULL_POSITION, end=NULL_POSITION, space_after=False,
                 add_space_after=False, index=0):
        ''' Generic init all tokens share. '''
        # Init fields for rendering.  By default
        # add spaces after each macro token when rendering.
        self.init_render_base(render_space_after=True, js=True)
        
        # Stored as named arguments for external access.
        self.token_type      = token_type
        self.token_id        = token_id
        self.data            = data
        self.start           = start
        self.end             = end
        self.index           = index
        self.attrs           = None
        self.space_after     = space_after
        # add_space_after is whether or not the token should have
        # a space added after to function
        self.add_space_after = add_space_after
        self.data_type       = None
        # Boolean marker whether not this token was constructed
        # due to the presence of another token.
        self.added           = False
        

        # Handle encoding and remove extra spaces in the data if
        # needed.
        if data is not None:
            # Check data type.
            if is_number(self.data):
                self.data_type = int
            else:
                self.data_type = str
                data = self.space_norm_re.sub(' ', data)


        # Handle lowercasing for some tokens that don't
        # need their own specific class.

        # This is a bit of a hack, but simple to do it here.

        # TODO: do this when saving the token in rules.
        
        if token_type == TARGET or token_type == MODIFIER:
            self.data = self.data.lower()

        # If there's a toggle, add a short default warning message
        if token_type == TOGGLE: self.warn = (WARN_TOGGLE,)

    def get_reconstructed_token_str(self):
        ''' Get cleaned token data back for display '''
        ret_str = self.data

        # If it came with a space after, then it gets one back
        if self.space_after:
            ret_str = ret_str + ' '
        
        return ret_str

    #
    # Rendering Helpers
    #

    # Get the type of this token.
    def get_token_type(self):
        return self.token_type

    # Get the text description used to render this token.
    # Overrides base class.
    def get_render_desc(self):
        if self.render_desc: return self.render_desc
        if self.attrs and self.attrs.desc:  return self.attrs.desc
        return self.name()


    # Is there external wow data for this token?
    def found(self):
        try:
            return self.attrs.param_data_obj.found()
        except:
            return False

    # A few shortcuts
    def slot(self):
        try:
            return self.attrs.param_data_obj.get_slot()
        except:
            return None
    def name(self):
        try:
            self.attrs.param_data_obj.get_name()
        except:
            pass
        return self.data
        

    #
    # Utility Functions
    #

    def is_type(self, token_type=None):
        ''' Simple type check. '''
        return (token_type == self.token_type)
