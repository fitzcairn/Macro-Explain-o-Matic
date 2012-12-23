''' Language specification for the WoW Macro language.

Options.
'''
from macro.language.base import LanguagePart
from macro.interpret.assemble_functions import *

# Class describing Options
class Option(LanguagePart):
    ''' Class describing option characteristics.  In addition to
    fields in LanguagePart, the following describe an Option:
    
    action: (Optional)
    Whether or not this conditional checks an action, i.e. what
    button was used to activate the macro.
    Default: False.

    def_target: (Optional)
    The default target this option refers to.
    Default is player.

    ext_target: (Optional)
    Whether or not this option can refer to an external target.  False
    means it ONLY applies to self, regardless of the target used in
    the macro.  Examples of options that dont require external targets
    are modifier:X or button:
    Default False

    no_args: (Optional)
    Option can NOT take arguments. Example: stealth
    Default True

    req_args: (Optional)
    Option requires arguments and is incorrect without them,
    i.e. button:X
    Default False

    req_num_arg: (Optional)
    Option arguments must be numeric
    Default False.  

    can_be_arg: (Optional)
    Option can ALSO be an argument, i.e. [party] -> [group:party]
    Default False

    req_join: (Optional)
    Whether or not the option requires a join word for the target,
    i.e. "you ARE in combat" or "you activate" (no join)
    Default True

    can_take_spell: (Optional)
    Whether or not the argument for this option is a spell or item we can
    look up for more information.
    Default False
    '''
    attr_defaults = {
        'def_target'        : 'player',
        'action'            : False,
        'ext_target'        : False,
        'req_args'          : False, 
        'req_num_arg'       : False, 
        'can_be_arg'        : False, 
        'req_join'          : True, 
        'can_take_spell'    : False,
        'assemble_function' : get_assembled_option,
        'no_args'           : True,
        }
    

''' Map of available options '''
OPTION_MAP = {
    'help':       Option(desc='a friend', ext_target=True, def_target='target'),
    'harm':       Option(desc='an enemy', ext_target=True, def_target='target'),
    'exists':     Option(desc='exist',  ext_target=True, def_target='target', req_join=False, assemble_function=get_exists_option),
    'dead':       Option(desc='dead', ext_target=True, def_target='target'),
    'stance':     Option(desc='stance', no_args=False, req_num_arg=True, assemble_function=get_stance_option),
    'spec':       Option(desc='spec', no_args=False, req_join=False, req_args=True, req_num_arg=True, assemble_function=get_spec_option),
    'form':       Option(desc='form', no_args=False, req_num_arg=True, assemble_function=get_stance_option),
    'stealth':    Option(desc='stealthed'),
    'modifier':   Option(desc='holding', no_args=False, req_join=False, assemble_function=get_mod_option),
    'mod':        Option(desc='holding', no_args=False, req_join=False, assemble_function=get_mod_option),
    'button':     Option(desc='activated this macro with', action=True, no_args=False, req_args=True, req_join=False, req_num_arg=True, assemble_function=get_btn_option),
    'btn':        Option(desc='activated this macro with', action=True, no_args=False, req_args=True, req_join=False, req_num_arg=True, assemble_function=get_btn_option),
    'equipped':   Option(desc='equipped item or itemtype', no_args=False, req_args=True, can_take_spell=False, req_join=False, assemble_function=get_equipped_option),
    'worn':       Option(desc='wearing item or itemtype', no_args=False, req_args=True, can_take_spell=False, req_join=False, assemble_function=get_worn_option),
    'channeling': Option(desc='channeling', no_args=False, can_take_spell=True, assemble_function=get_channeling_option),
    'bar':        Option(desc='have actionbar', no_args=False, req_args=True, req_join=False, req_num_arg=True, assemble_function=get_bar_option),
    'actionbar':  Option(desc='have actionbar', no_args=False, req_args=True, req_join=False, req_num_arg=True, assemble_function=get_bar_option),
    'bonusbar':   Option(desc='have bonusbar', no_args=False, req_args=True, req_join=False, req_num_arg=True, assemble_function=get_bar_option),
    'pet':        Option(desc='have a pet named or of type', no_args=False, req_join=False, assemble_function=get_pet_option),
    'combat':     Option(desc='in combat'),
    'mounted':    Option(desc='mounted'),
    'swimming':   Option(desc='swimming'),
    'flying':     Option(desc='flying'),
    'flyable':    Option(desc='in a zone allowing flying'),
    'indoors':    Option(desc='indoors'),
    'outdoors':   Option(desc='outdoors'),
    'party':      Option(desc='in your party', ext_target=True, can_be_arg=True, def_target='target'),
    'raid':       Option(desc='in your raid', ext_target=True, can_be_arg=True, def_target='target'),
    'group':      Option(desc='in a group', no_args=False, assemble_function=get_group_option),

    # New with 3.3
    'vehicleui':  Option(desc='have a vechicle UI', req_join=False),
    'unithasvehicleui':  Option(desc='has a vehicle UI', ext_target=True, def_target='target', req_join=False),
    }
