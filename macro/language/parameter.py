''' Language specification for the WoW Macro language.

Parameters
'''
from macro.language.base import LanguagePart

# Switch Appenging parameter lookups on and off.
DB_PARAM_LOOKUPS = False

# Class describing Parameters
class Parameter(LanguagePart):
    ''' Class describing macro Parameters.
    In addition to fields in LanguagePart, the following
    describe a Parameter:

    is_empty: (Optional)
    Parameter is an empty one.
    Default False

    param_data_obj: (Optional)
    Reference to a parameter-specific object describing this
    parameter, i.e. an Item or Spell object.
    Default None

    self_only: (Optional)
    Whether or not this parameter refers to the player only.
    Default False

    is_item_id_param: (Optional)
    Whether or not this parameter is an item_id.
    Default False
    '''
    attr_defaults = {
        'is_empty'         : False,
        'param_data_obj'   : None,
        'is_item_id_param' : False,
        'self_only'        : False,
        }

    # TODO: If we have a param_data_obj, use that name for the desc.


        
''' Map of known parameters inherent to the game. '''
PARAM_MAP = {
    'StaticPopup1Button':        Parameter(desc="the dialog box", self_only=True),
    'ActionButton':              Parameter(desc="the main bar", self_only=True),
    'BonusActionButton':         Parameter(desc="the bonus (stance/stealth) bar", self_only=True),
    'MultiBarBottomLeftButton':  Parameter(desc="the bottom left bar", self_only=True),
    'MultiBarBottomRightButton': Parameter(desc="the bottom right bar", self_only=True),
    'MultiBarRightButton':       Parameter(desc="the right bar", self_only=True),
    'MultiBarLeftButton':        Parameter(desc="the leftmost right bar", self_only=True),
    'PetActionButton':           Parameter(desc="the pet bar", self_only=True),
    'ShapeshiftButton':          Parameter(desc="the Form/Aura/Stance/Presence/Stealth bar", self_only=True),
    'LeftButton':                Parameter(desc="the left mouse button"),
    'RightButton':               Parameter(desc="the right mouse button"),
    'MiddleButton':              Parameter(desc="the middle mouse button"),
    'Button4':                   Parameter(desc="mouse button 4"),
    'Button5':                   Parameter(desc="mouse button 5"),
    'Button6':                   Parameter(desc="mouse button 6"),
    'Button7':                   Parameter(desc="mouse button 7"),
    'Button8':                   Parameter(desc="mouse button 8"),
    'Button9':                   Parameter(desc="mouse button 9"),
    'Button10':                  Parameter(desc="mouse button 10"),
    'none':                      Parameter(desc="nothing", is_empty=True),
    '':                          Parameter(desc="nothing", is_empty=True),
    }
