'''
Macro base class.
'''

from macro.lex.ids              import PARAMETER, INTERPRETER_TEXT

# Base class.  Only defines a render_init function.
class MacroTokenBase:
    """MacroTokenBase

    Contains rendering and untility members shared across
    MacroTokens and TxtTokens.

    Rendering-specific members:
      render_desc -- Display text for the token object,
                     overrides token.data.
      wowhead      -- Display wowhead links
      js           -- Enable javascript highlighting
      strike       -- Strike out tokens the interpreter marks as useless
      render_space_after -- self-explanatory!
    """
    def init_render_base(self,
                         render_desc=None,
                         js=False,
                         highlight=False,
                         wowhead=False,
                         strike=False,
                         render_space_after=True):
        # Data fields for rendering.
        self.error              = None
        self.warn               = None
        self.render_desc        = render_desc
        self.error_desc         = None
        self.js                 = js
        self.highlight          = highlight
        self.wowhead            = wowhead
        self.strike             = strike
        self.render_space_after = render_space_after
        self.index              = -1   # Default for TxtTokens.
        self.added              = True # Default for TxtTokens.

        
    #
    # Rendering Helpers
    #

    # Get the text description used to render this token.
    # Will be overridden in MacroToken
    def get_render_desc(self):
        return self.render_desc
    def get_error_desc(self):
        if self.error_desc: return self.error_desc
        if self.data: return self.data
        return self.get_render_desc()
    def is_param(self):
        return self.token_type == PARAMETER
    def get_token_type(self):
        # Default: added by interpreter
        return INTERPRETER_TEXT


    #
    # Utility Rendering Functions
    #

    def get_list(self):
        ''' Array representation, for convienience.'''
        return [self.token_type,
                self.token_id,
                self.data,
                self.start,
                self.end,
                self.space_after]
    def get_str(self):
        if self.render_space_after:
            return self.get_render_desc() + " "
        return self.get_render_desc()
    def __str__(self):
        return str(self.get_list())
    def __repr__(self):
        return str(self.get_list())

