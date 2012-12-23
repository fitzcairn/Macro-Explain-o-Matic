''' Language specification for the WoW Macro language.

Option arguments.
'''

from macro.language.base import LanguagePart

# Class describing Argument attributes.
class Arg(LanguagePart):
    ''' Class describing arguments.
    In addition to fields described in LanguagePart,
    we have the following attributes:

    param_data_obj: (Optional)
    Reference to a parameter-specific object describing this
    parameter, i.e. an Item or Spell object.
    Default None
    
    is_key: (Optional)
    Whether or not this argument is a keypress.
    Default False.

    is_reset_arg: (Optional)
    Whether or not this argument can be used in a reset command.
    Default False.

    is_option_arg: (Optional)
    Whether or not this argument can be used as an option argument.
    Default True.

    warn: (Optional)
    A default warning to assign this option arg.
    Default None.

    new_target: (Optional)
    Some keys change the target of the macro, for example FOCUSCAST.
    Default None.
    '''
    attr_defaults = {
        'is_key'        : False,
        'is_reset_arg'  : False,
        'is_option_arg' : True,
        'param_data_obj': None,
        'warn'          : None,
        'new_target'    : None,
        }

    # TODO: If we have a param_data_obj, use that name for the desc.



''' Map of known argument types. '''
ARG_MAP = {
    'shift':            Arg(desc="shift key", is_key=True, is_reset_arg=True),
    'alt':              Arg(desc="alt key", is_key=True, is_reset_arg=True),
    'ctrl':             Arg(desc="control key", is_key=True, is_reset_arg=True),
    'FOCUSCAST':        Arg(desc="focus-cast key", is_key=True, new_target="focus", warn="Using FOCUSCAST changes the command target to your focus target, which must exist."),
    'SELFCAST':         Arg(desc="self-cast key (def: alt)", new_target="player", is_key=True, warn="Using SELFCAST changes the command target to you."),
    'AUTOLOOTTOGGLE':   Arg(desc="auto-loot key (def: shift)", is_key=True),
    'STICKYCAMERA':     Arg(desc="sticky-camera key (def: control)", is_key=True),
    'SPLITSTACK':       Arg(desc="split-stack key (def: shift)", is_key=True),
    'PICKUPACTION':     Arg(desc="pick-up-action key (def: shift)", is_key=True),
    'COMPAREITEMS':     Arg(desc="compare-items key (def: shift)", is_key=True),
    'OPENALLBAGS':      Arg(desc="open-all-bags key (def: shift)", is_key=True),
    'QUESTWATCHTOGGLE': Arg(desc="quest watch toggle key (def: shift)", is_key=True),
    'combat':           Arg(desc="you leave combat", is_reset_arg=True, is_option_arg=False),
    'party':            Arg(desc="party"),
    'raid':             Arg(desc="raid"),
    'target':           Arg(desc="you change targets", is_reset_arg=True, is_option_arg=False),
    'LeftButton':       Arg(desc="the left mouse button"),
    'RightButton':      Arg(desc="the right mouse button"),
    'MiddleButton':     Arg(desc="the middle mouse button"),
    'Button4':          Arg(desc="mouse button 4"),
    'Button5':          Arg(desc="mouse button 5"),
    'Button6':          Arg(desc="mouse button 6"),
    'Button7':          Arg(desc="mouse button 7"),
    'Button8':          Arg(desc="mouse button 8"),
    'Button9':          Arg(desc="mouse button 9"),
    'Button10':         Arg(desc="mouse button 10"),
    }
