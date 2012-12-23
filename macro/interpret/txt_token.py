'''
Objects for txt-only tokens.
'''

from macro.lex.token_base import MacroTokenBase
from macro.util           import NULL_POSITION, NULL_TOKEN_ID
       

class TxtToken(MacroTokenBase):
    ''' Simple token for rendering.  Shares parent object
    with MacroToken.

    TxtToken allows the creation of light-weight objects
    for rendering non-macro interpretation text.'''

    def __init__(self, txt,
                 js=False,
                 highlight=False,
                 wowhead=False,
                 strike=False,
                 render_space_after=True):

        # Init some token fields for sharing str and repr with
        # MacroToken.
        self.start       = NULL_POSITION
        self.end         = NULL_POSITION
        self.token_id    = NULL_TOKEN_ID
        self.token_type  = "TXT"
        self.space_after = render_space_after
        self.data        = txt
        self.data_type   = str

        # Init fields for rendering
        self.init_render_base(render_desc=txt,
                              js=js,
                              highlight=highlight,
                              wowhead=wowhead,
                              strike=strike,
                              render_space_after=render_space_after)
